echo "Give the Dell XPS 16 (NVIDIA N1x) the RAM its firmware reserves for Windows' GPU"

# See installer/hardware/fix-n1x-gpu-memory.sh. The kernel option takes effect
# with linux-n1x; older N1x kernels ignore it.
dropin="${ARCH_N1X_GPU_MEMORY_CONF:-/etc/limine-entry-tool.d/arch-n1x-gpu-memory.conf}"
iomem="${ARCH_IOMEM:-/proc/iomem}"
running_cmdline="${ARCH_RUNNING_CMDLINE:-/proc/cmdline}"
rebuild_marker="${ARCH_LIMINE_REBUILD_MARKER:-/var/lib/arch/migrations/1790984400}"

if ! arch-hw-match "DX16263"; then
  exit 0
fi

if [[ ! -f $dropin ]]; then
  # /proc/iomem only shows addresses to root.
  sudo grep -qx '1fd000000-119fffffff : reserved' "$iomem" || exit 0

  sudo install -Dm644 /dev/stdin "$dropin" <<'CONF'
# NVIDIA N1x: use the idle part of the firmware's Windows GPU memory as RAM; see
# installer/hardware/fix-n1x-gpu-memory.sh.
KERNEL_CMDLINE[default]+=" efi_reclaim_reserved=58G@8G"
CONF
fi

# The running kernel keeps its command line until reboot, so a marker records
# the machine-wide rebuild: another user's run must not repeat it, while a
# missing marker still retries an interrupted rebuild.
[[ ! -e $rebuild_marker ]] || exit 0
[[ " $(<"$running_cmdline") " != *" efi_reclaim_reserved="* ]] || exit 0

sudo limine-mkinitcpio
sudo install -Dm644 /dev/null "$rebuild_marker"
