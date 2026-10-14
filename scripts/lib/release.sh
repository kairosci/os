#!/usr/bin/env bash

kos_release_profile() {
    local project="$1" profile="$2" package="$3" releng="$4" version repository file
    local strip_tmp stripped_pkg _iso_entries
    version=$(kos_version "$project") || return 1
    [[ ! -e "$profile" && -f "$package" && -f "$releng/profiledef.sh" ]] || return 1
    cp -a "$releng" "$profile" || return 1
    repository="${profile%/*}/repository"
    install -d -m 755 "$repository"
    strip_tmp=$(mktemp -d) || return 1
    stripped_pkg="$repository/$(basename "$package")"
    bsdtar -C "$strip_tmp" -xf "$package" || { rm -rf "$strip_tmp"; return 1; }
    if [[ -f "$strip_tmp/etc/skel/.bashrc" ]]; then
        install -Dm644 "$strip_tmp/etc/skel/.bashrc" "$profile/airootfs/etc/skel/.bashrc" || { rm -rf "$strip_tmp"; return 1; }
        rm -f "$strip_tmp/etc/skel/.bashrc"
    fi
    mapfile -d '' _iso_entries < <(cd "$strip_tmp" && find . \! \( -name .PKGINFO -o -name .MTREE \) -mindepth 1 -print0 | sort -z)
    local _meta=()
    [[ -f "$strip_tmp/.PKGINFO" ]] && _meta+=(.PKGINFO)
    [[ -f "$strip_tmp/.MTREE" ]] && _meta+=(.MTREE)
    bsdtar --format=gnutar -C "$strip_tmp" -cf - "${_meta[@]}" "${_iso_entries[@]}" | zstd -T0 > "$stripped_pkg" || { rm -rf "$strip_tmp"; return 1; }
    rm -rf "$strip_tmp"
    repo-add "$repository/kos.db.tar.gz" "$stripped_pkg" || return 1
    printf '\n[kos]\nSigLevel = Optional TrustAll\nServer = file://%s\n' "$repository" >> "$profile/pacman.conf" || return 1
    install -d -m 755 "$profile/airootfs"
    for file in etc/os-release etc/mkinitcpio.conf.d/kos_hooks.conf etc/pacman.d/hooks/90-mkinitcpio-install.hook etc/skel/.bashrc; do
        sed -i "/^\[options\]/a NoExtract = $file" "$profile/pacman.conf" || return 1
    done
    install -d -m 755 "$profile/airootfs/etc/pacman.d/hooks"
    for file in 10-limine-snapper-lock.hook 60-limine-mkinitcpio-remove-pre.hook 80-limine-efi-deploy.hook 90-limine-mkinitcpio-remove-post.hook; do
        ln -s /dev/null "$profile/airootfs/etc/pacman.d/hooks/$file" || return 1
    done
    install -d -m 755 "$profile/airootfs/opt/kos"
    cp "$package" "$profile/airootfs/opt/kos/" || return 1
    cat "$project/conf/kos/data/runtime-packages.list" "$project/conf/kos/data/iso-packages.list" >> "$profile/packages.x86_64" || return 1
    printf 'kos\nlinux\nlinux-headers\n' >> "$profile/packages.x86_64" || return 1
    LC_ALL=C sort -u "$profile/packages.x86_64" -o "$profile/packages.x86_64" || return 1
    cat >> "$profile/profiledef.sh" <<PROFILE
iso_name="kos"
iso_label="KOS_${version//./_}"
iso_publisher="kos <https://github.com/kairosci/kos>"
iso_application="kos installation medium"
iso_version="$version"
PROFILE
    printf 'kos\n' > "$profile/airootfs/etc/hostname" || return 1
    cp "$project/conf/kos/data/iso-motd" "$profile/airootfs/etc/motd" || return 1
    install -Dm755 "$project/conf/kos/data/install-system.sh" "$profile/airootfs/usr/bin/kos-install-system" || return 1
    install -Dm644 "$project/conf/kos/data/boot-check.service" "$profile/airootfs/etc/systemd/system/kos-boot-check.service" || return 1
    install -d -m 755 "$profile/airootfs/etc/systemd/system/multi-user.target.wants"
    ln -s ../kos-boot-check.service "$profile/airootfs/etc/systemd/system/multi-user.target.wants/kos-boot-check.service" || return 1
    source "$project/scripts/lib/os-identity.sh"
    install -d -m 755 "$profile/airootfs/usr/lib"
    printf 'ID=arch\n' > "$profile/airootfs/usr/lib/os-release" || return 1
    kos_identity_apply "$profile/airootfs" "$version" || return 1
    rm "$profile/airootfs/usr/lib/os-release" || return 1
    rm -rf "$profile/airootfs/var/lib/kos/os-identity"
}

kos_release_build() {
    local project="$1" output="$2" package work tool
    [[ $EUID -eq 0 ]] || err release.root
    for tool in mkarchiso bsdtar zstd repo-add; do
        command -v "$tool" >/dev/null || err release.tools "$tool"
    done
    package=$(kos_package_build "$project" "$output") || err release.invalid
    source "$project/scripts/lib/release-manifest.sh"
    kos_manifest_create "$output" "$(kos_version "$project")" || err release.invalid
    cp "$project/conf/kos/data/packages/boot-tools/"*.src.tar.gz "$output/"
    work=$(mktemp -d "$output/.iso.XXXXXX") || err release.invalid
    kos_release_profile "$project" "$work/profile" "$package" /usr/share/archiso/configs/releng || err release.invalid
    mkarchiso -v -w "$work/work" -o "$output" "$work/profile"
    (
        cd "$output" || exit 1
        sha256sum -- kos-*.pkg.tar.zst *.src.tar.* kos-*.iso > SHA256SUMS
    )
    rm -rf "$work"
    chmod 644 "$output"/kos-*.pkg.tar.zst "$output"/kos-*.iso "$output/SHA256SUMS"
    log release.done "$output"
}
