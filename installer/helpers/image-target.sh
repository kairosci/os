# Image builds and the hardware setup they defer to the machine's first boot.
# Sourced by arch-apply-hardware and arch-provision-hardware; no shebang.
#
# An image is built away from the machine it will run on, so hardware setup
# during the build would describe the builder, not the target. The builder
# declares the build in a root-owned manifest before it runs
# arch-apply-system in the image root:
#
#   /var/lib/arch/image/target
#     format=1
#     platform=x86|aarch64|aarch64-apple|aarch64-qualcomm|aarch64-n1x|aarch64-gb10
#
# While it exists, arch-apply-hardware queues each hardware leaf in
# /var/lib/arch/image/deferred-steps instead of running it, and arms
# arch-provision-hardware.service. On the machine's first boot that service,
# or the platform's own first boot, retires the manifest (to target.booted) and
# runs the queue on the real hardware. Unknown manifest keys are ignored so the
# format can grow.
#
# An image carries no pacman master key of its own, or every machine flashed
# from it would share one: where install finalization would make the keyring
# (src/python/installer/post_install/pacman.py), a build requests it in
# /var/lib/arch/image/pacman-keyring instead, and the first boot makes it
# before any deferred step runs.
#
# The manifest is also the only source of the image's platform: until that boot,
# arch-hw-platform reports its platform instead of the build host's, so the
# initramfs, services and packages the build sets up are the target's. It reads
# the manifest by the same rules as arch_image_read_manifest below.
#
# Root always uses the fixed paths. Only a non-root test may move them under
# ARCH_IMAGE_ROOT, so no environment variable can make a live system defer,
# skip or replay its hardware setup.

arch_image_init() {
  if (( EUID == 0 )); then
    arch_image_root=""
  elif [[ -n ${ARCH_IMAGE_ROOT:-} ]]; then
    arch_image_root=$ARCH_IMAGE_ROOT
  else
    echo "Error: image setup state is root-owned; run as root" >&2
    return 1
  fi

  arch_image_dir=$arch_image_root/var/lib/arch/image
  arch_image_manifest=$arch_image_dir/target
  arch_image_queue=$arch_image_dir/deferred-steps
  arch_image_initramfs_baseline=$arch_image_dir/initramfs-inputs
  arch_image_boot_rebuild=$arch_image_dir/boot-rebuild
  arch_image_keyring_request=$arch_image_dir/pacman-keyring
  arch_image_unit=arch-provision-hardware.service
  arch_image_systemd_dir=$arch_image_root/etc/systemd/system
}

# Owned by whoever runs this (root on a live system), not a symlink, and not
# writable by anyone else.
arch_image_trusted() {
  local path=$1 owner mode

  [[ -e $path && ! -L $path ]] || return 1
  read -r owner mode < <(stat -c '%u %a' -- "$path") || return 1
  (( owner == EUID && (8#$mode & 8#022) == 0 ))
}

arch_image_manifest_present() {
  [[ -e $arch_image_manifest || -L $arch_image_manifest ]]
}

# Sets arch_image_platform, or fails without guessing whether this is a build.
arch_image_read_manifest() {
  local line key value format="" platform=""

  if [[ ! -d $arch_image_dir || ! -f $arch_image_manifest ]] || ! arch_image_trusted "$arch_image_dir" ||
    ! arch_image_trusted "$arch_image_manifest"; then
    echo "Error: $arch_image_manifest is not a root-owned regular file" >&2
    return 1
  fi

  while IFS= read -r line || [[ -n $line ]]; do
    [[ -n $line && $line != \#* ]] || continue
    if [[ $line != *=* ]]; then
      echo "Error: $arch_image_manifest is malformed: $line" >&2
      return 1
    fi
    key=${line%%=*}
    value=${line#*=}
    case $key in
      format) format=$value ;;
      platform) platform=$value ;;
    esac
  done <"$arch_image_manifest"

  if [[ $format != "1" ]]; then
    echo "Error: $arch_image_manifest is not format=1" >&2
    return 1
  fi
  # Builders written before the platform names settled say apple-silicon,
  # generic-aarch64, generic or qualcomm (as arch-hw-platform reads them too).
  case $platform in
    apple-silicon) platform=aarch64-apple ;;
    generic-aarch64) platform=aarch64 ;;
    generic) platform=x86 ;;
    qualcomm) platform=aarch64-qualcomm ;;
  esac
  case $platform in
    x86 | aarch64 | aarch64-apple | aarch64-qualcomm | aarch64-n1x | aarch64-gb10) ;;
    *)
      echo "Error: $arch_image_manifest names no known platform: ${platform:-none}" >&2
      return 1
      ;;
  esac

  arch_image_platform=$platform
}

# Holds the image state still for the rest of the caller, so hardware setup and
# a first-boot run never overlap or decide from a manifest the other retires.
# A machine that was never an image has no state and nothing to lock.
arch_image_lock() {
  [[ -e $arch_image_dir || -L $arch_image_dir ]] || return 0
  if [[ ! -d $arch_image_dir ]] || ! arch_image_trusted "$arch_image_dir"; then
    echo "Error: $arch_image_dir is not a root-owned directory" >&2
    return 1
  fi
  exec {arch_image_lock_fd}>>"$arch_image_dir/lock" || return 1
  flock "$arch_image_lock_fd"
}

arch_image_write_queue() {
  local tmp

  tmp=$(mktemp "$arch_image_dir/.deferred-steps.XXXXXX") || return 1
  if (( $# )); then
    printf '%s\n' "$@" >"$tmp" || { rm -f "$tmp"; return 1; }
  fi
  chmod 0644 "$tmp" && mv -f "$tmp" "$arch_image_queue"
}

# Queue every configured hardware leaf in order, running none of them, then
# arm the first-boot service. Rerunning rewrites the same queue.
arch_image_defer_hardware() {
  local listing
  local -a steps=()

  listing=$(python3 -I "$ARCH_PATH/src/python/installer/step_runner.py" --list data/installer/hardware-setup.yml) || return 1
  if [[ -n $listing ]]; then
    while IFS= read -r step; do
      [[ $step == installer/hardware/*.sh && $step != *..* ]] ||
        [[ $step == src/python/installer/hardware/*.py && $step != *..* ]] || {
          echo "Error: cannot defer a step outside the hardware setup: $step" >&2
          return 1
        }
      steps+=("$step")
    done <<<"$listing"
  fi

  arch_image_write_queue "${steps[@]}" || return 1

  install -d -m 0755 "$arch_image_systemd_dir/multi-user.target.wants" &&
    install -m 0644 "$ARCH_INSTALL/provisioning/$arch_image_unit" "$arch_image_systemd_dir/$arch_image_unit" &&
    ln -sfn "/etc/systemd/system/$arch_image_unit" "$arch_image_systemd_dir/multi-user.target.wants/$arch_image_unit" ||
    return 1

  echo "Image build for $arch_image_platform: deferred ${#steps[@]} hardware steps to first boot"
}
