# File layout

How `arch/` is organized and where everything ends up on an installed
system.

## Mental model

Two Arch packages are built from this one repo (PKGBUILDs live in the
separate `arch-pkgs` repository, under `pkgbuilds/`):

- **`arch`** — CLI sources (`src/cli/`), installed as runtime binaries under `bin/` (including `arch-dev-*`),
  installer/finalize scripts (`installer/`), migrations, themes, and the
  Quickshell desktop (`src/shell/`). Depends on `arch-settings`.
- **`arch-settings`** — everything that has to be on the target *before*
  the archctl package installs (specifically before `useradd -m` and the
  limine bootloader install): all `/etc/skel/**`, `/etc/` drop-ins,
  package-owned system files under `/usr/share` and `/usr/lib`, fonts,
  plymouth theme, sddm theme, branding, plus the limine/snapper configs
  (mkinitcpio hooks, limine-entry-tool drop-ins, snapper template, the
  `default/limine/` and `default/snapper/` trees, and the boot/snapshot
  story end-to-end). Also ships the three debug binaries
  (`arch-debug`, `arch-debug-idle`, `arch-upload-log`) needed by
  the live ISO env.

Two other packages live in `arch-pkgs` but stand alone:
`arch-keyring` (GPG keys for pacman) and `neovim` (the Neovim
setup; independently seeds `/etc/skel`).

Some trees ship in neither package and exist only in the repo: `docs/user/`
(user manual chapters), `agents/skills/` (contributor task guides), `docs/`,
`tests/`, and `plans/`.

Three layers populate `$HOME`:

1. **Seed** — `arch-settings` ships static defaults to `/etc/skel/`.
   Arch's `useradd -m` copies that tree into a new user's `$HOME` at user
   creation. This is the only mechanism that touches a brand-new user's home
   for these files.
2. **Finalize** — `arch-provision-user` (routed as `arch finalize
   user`) runs once per user and handles the things `/etc/skel` can't do
   because they need `$HOME` expansion, the live `$ARCH_PATH`, or runtime
   detection of system state.
3. **Resync** — `arch-reinstall-configs` is the explicit, destructive
   command for an existing user to clobber their configs back to shipped
   defaults.

`/etc/skel` only fires at user creation. Existing users picking up new
defaults must use the resync command.

Deferred-provisioning installs (`arch-apply-system --defer-provisioning`)
create no user at all: the ISO leaves `/var/lib/arch/provisioning/pending`
behind, which arms `arch-provision-owner.service` (shipped from
`installer/provisioning/`, alongside the factory-reset finish unit and
`setup-form.sh`). On first boot `src/cli/arch-provision-owner` creates the
user on tty1 and runs the finalize step itself.

On an encrypted install `arch-provision-owner` then re-keys LUKS from the staged install key to the owner's password through `installer/provisioning/luks-rekey.sh`, which journals each step (phase and slot numbers, never keys) in `/var/lib/arch/provisioning/luks-rekey.state` so an interrupted first boot resumes. Setup finishes only once the staged key opens nothing, and removes the journal with `pending`, so a retry after the staged key is retired must use the password the disk holds. On a platform whose boot package owns the boot chain, the check before the owner form, the boot-time unlock and the record of the kept key slot go through `arch-lifecycle-dispatch`. See [lifecycle-dispatch.md](lifecycle-dispatch.md).

`arch-drive-password` reuses those journal helpers when the owner changes the password of the disk holding `/`: it changes the LUKS key and confirms the new key opens the disk and the old one no longer does. The login and root passwords are left alone. `~/.local/state/arch/drive-password.state` records the disk's UUID, the key slots and the phase (never a password) until the change is confirmed and its slot recorded, and the next run finishes an interrupted change with whichever of the old or new password the disk opens with.

Prebuilt images are set up away from the machine they will run on, so their hardware setup waits for that machine. The builder writes a root-owned manifest, `/var/lib/arch/image/target` (`format=1`, `platform=<arch-hw-platform value>`), before `arch-apply-system`. While it exists, `arch-apply-hardware` runs no hardware leaf: it queues each one in `/var/lib/arch/image/deferred-steps` and arms `arch-provision-hardware.service` (shipped from `installer/provisioning/`). On the machine's first boot, before owner setup and the login screen, `src/cli/arch-provision-hardware` renames the manifest to `target.booted` and runs the queue in order, dropping each step that succeeds. Before the first step it makes the machine's own pacman keyring when the build asked for one (`/var/lib/arch/image/pacman-keyring`, which install finalization writes on aarch64 platforms other than Apple Silicon instead of running `pacman-key --init`, so no two machines share a master key). A failed step stays queued for the next boot. It refreshes no package databases: the image carries its sync databases and every package its queued steps install, so the queue runs offline (the image build checks that it carries them; a step whose package is missing stays queued). Once the queue is empty it rebuilds the initramfs if a step changed its inputs (the mkinitcpio configuration, module options in `/etc/modprobe.d/` and `/usr/lib/modprobe.d/`, or the kernel command line in `/etc/default/limine` and `/etc/limine-entry-tool.d/`) or asked for the rebuild (`/var/lib/arch/image/boot-rebuild`), and disables the service; the unit file stays, so a start job already queued is skipped on the emptied queue rather than failed. A platform's own first boot may run `arch-provision-hardware` itself: runs are serialised, and it exits 75 when a step or the keyring failed and stays queued, and 1 when it refused to run (an untrusted manifest or queue) or the final rebuild failed, which the next run retries. Steps know they run on an image's first boot from `ARCH_IMAGE_DEFERRED_HARDWARE=1` (Bluetooth starts its service there, since boot already brought up its target). `installer/helpers/image-target.sh` holds the contract. Root always uses these fixed paths; no environment variable turns a live system into an image build.

Current generated theme state lives under
`~/.local/state/arch/current/`. Keep `~/.config/arch/` for files a user
may intentionally version in a dotfile manager, such as user themes, hooks,
shell layout, plugins, and themed template overrides.

## Build-time map (repo → installed paths)

```
arch/                            built into          installed at
─────────────────────────           ──────────────      ────────────────────────────────────

src/cli/arch-*              ──►  arch             /usr/bin/arch-*
                                                        (and symlinks in /usr/share/arch/src/cli/)
src/cli/arch-debug,
src/cli/arch-debug-idle,
src/cli/arch-upload-log     ──►  arch-settings    /usr/bin/  (needed before arch is installed)

default/libalpm/hooks/*.hook
                                ──►  arch             /usr/share/libalpm/hooks/*.hook

installer/**                     ──►  arch             /usr/share/arch/installer/
migrations/**                  ──►  arch             /usr/share/arch/migrations/
assets/themes/**                      ──►  arch             /usr/share/arch/assets/themes/
src/shell/**                       ──►  arch             /usr/share/arch/src/shell/
version                        ──►  arch             /usr/share/arch/version
                                                        + /etc/skel/.local/state/arch/migrations/*

config/**                      ──►  arch-settings    /etc/skel/.config/**         (seeds new users)
                                                        /usr/share/arch/config/** (resync source)
etc/fastfetch/config.jsonc     ──►  arch-settings    /etc/fastfetch/config.jsonc
etc/xdg/kitty/kitty.conf       ──►  arch-settings    /etc/xdg/kitty/kitty.conf
etc/mpv/mpv.conf               ──►  arch-settings    /etc/mpv/mpv.conf            (hardware decoding; ~/.config/mpv wins)
etc/xkb/{rules/evdev,symbols/arch}
                               ──►  arch-settings    /etc/xkb/                    (Shift + Caps Lock compose option)

assets/applications/*.desktop         ──►  arch-settings    /etc/skel/.local/share/applications/
                                                        /usr/share/arch/assets/applications/
default/applications/*.desktop
                                ──►  arch-settings    /usr/share/arch/default/applications/
                                                        (optional and legacy launcher templates)
assets/applications/icons/*           ──►  arch-settings    /usr/share/icons/hicolor/{48,256,scalable}/apps/

etc/**                         ──►  arch-settings    /etc/**           (drop-ins we own outright)
  ├─ mkinitcpio.conf.d/{00-arch-hooks,arch_hooks,thunderbolt_module}.conf
  ├─ limine-entry-tool.d/{arch-defaults,arch-uki}.conf
  ├─ mise/conf.d/{arch,arch-tools,arch-agent-accounts}.toml
  ├─ NetworkManager/, sudoers.d/, sysctl.d/, tmpfiles.d/,
  │  profile.d/arch.sh, …                            (a summary — `ls etc/` for the full ~17-entry tree)
  └─ security/faillock.conf, nsswitch.conf,
     cups/cups-browsed.conf, plymouth/plymouthd.conf    /usr/share/arch/etc-overrides/
                                                          → /etc/* (post_install cp -f, see below)

default/limine/limine.conf     ──►  arch-settings    /usr/share/arch/default/limine/limine.conf
default/limine/default.conf    ──►  arch-settings    /usr/share/arch/default/limine/default.conf
                                                        (template; ISO substitutes @@CMDLINE@@ → /etc/default/limine)
default/snapper/root           ──►  arch-settings    /etc/snapper/config-templates/arch
                                                        (+ /usr/share/arch/default/snapper/root)

default/**                     ──►  arch-settings    /usr/share/arch/default/
  ├─ bash/env-bootstrap                                 /usr/share/arch/default/bash/env-bootstrap
  │                                                       (sourced by every src/shell/session entry point; see "Env bootstrap")
  ├─ bashrc                                             /usr/share/arch/etc-overrides/dot.bashrc
  │                                                       → /etc/skel/.bashrc (post_install cp -f)
  ├─ hypr/toggles/*.lua (flags,
  │    single-window-aspect-ratio, window-no-gaps)      /etc/skel/.local/state/arch/toggles/hypr/
  ├─ nautilus-python/extensions/*.py                    /etc/skel/.local/share/nautilus-python/extensions/
  ├─ uwsm/env.d/10-arch                              /usr/share/uwsm/env.d/
  ├─ environment.d/*.conf                               /usr/lib/environment.d/
  ├─ fontconfig/conf.avail/50-arch.conf              /usr/share/fontconfig/conf.avail/
  │                                                       + symlink /etc/fonts/conf.d/50-arch.conf
  ├─ xdg-terminal-exec/*.list                           /usr/share/xdg-terminal-exec/
  ├─ applications/mimeapps.list                         /usr/share/applications/mimeapps.list
  ├─ systemd/user/*.service                             /usr/lib/systemd/user/
  ├─ systemd/user/app.slice.d/10-oomd.conf              /usr/lib/systemd/user/app.slice.d/
  ├─ systemd/system-sleep/unmount-fuse                  /usr/lib/systemd/system-sleep/
  ├─ systemd/zram-generator.conf.d/90-arch.conf      /usr/lib/systemd/zram-generator.conf.d/
  ├─ systemd/timesyncd.conf.d/10-arch.conf          /usr/lib/systemd/timesyncd.conf.d/
  ├─ fonts/arch/arch.ttf                          /usr/share/fonts/arch/
  ├─ sddm/arch/                                         /usr/share/sddm/themes/arch/
  ├─ sddm/hyprland.lua                                  /usr/share/sddm/hyprland.lua
  ├─ wayland-sessions/arch.desktop                      /usr/local/share/wayland-sessions/
  └─ plymouth/                                          /usr/share/plymouth/themes/arch/

logo.{txt,svg}, icon.{txt,png}  ──► arch-settings    /usr/share/arch/  (resync source)
                                                        /usr/share/pixmaps/arch.png
                                                        /usr/share/icons/hicolor/256x256/apps/arch.png
                                                        /etc/skel/.config/arch/branding/{about,screensaver}.txt
```

The hardware-conditional `force-igpu` and `keyboard-backlight` sources also live under `default/systemd/system-sleep/`, but their setup commands publish root-owned copies only on machines that need them; they are not installed by `arch-settings`.

### Platform root

A platform's runtime package (arch-mac on Apple Silicon, say) adds its desktop files under a fixed root that only the one installed platform package owns. Arch ships nothing there, and a missing root or file means no platform additions. No environment variable moves it; tests reach fixtures through test-only seams, never through a desktop session's environment.

```
/usr/share/arch-platform/
  displays.conf                backlight and DDC hints for the display commands (below)
  key-names                    "<keysym> <name>" lines the keybindings menu shows in place of keysyms
  display-cutouts.json         camera cutouts the top bar keeps out of (see arch-shell.md)
  keyrings                     signing keyring packages of the repositories the platform adds, one per line
  audio.json                   audio processing nodes the audio panel and microphone widget leave out (below)
  fingerprint-readers          readers the kernel drives without USB, and the file that shows each one is usable (below)
```

See [lifecycle-dispatch.md](lifecycle-dispatch.md#platform-files).

`arch-update-keyring` refreshes each installed package `keyrings` names (`#` comments and blank lines skipped, and a line that isn't a `*-keyring` package name skipped with a warning) along with Arch's, before the system upgrade, installing any newer version the repository has, so a key rotation in the platform's own repository never fails that upgrade's signature checks. On Apple Silicon, arch-mac names `asahi-alarm-keyring` there.

#### Display hints (`displays.conf`)

`arch-hw-display` picks the built-in panel's backlight by name (`gmux_backlight`, then `amdgpu_bl*`, `intel_backlight`, `acpi_video*`, else the first one listed, never a T2 Touch Bar's `appletb_backlight`), and `arch-brightness-display` probes every external monitor over DDC. Where a platform's names or display driver differ, its platform package says so in `/usr/share/arch-platform/displays.conf`; Arch ships none, and without it both behave as above. One directive per line, whitespace-separated; blank lines, whole-line `#` comments, unknown directives, and lines with a wrong word count or a name that is `.`, `..` or has a `/` are ignored:

- `backlight-skip <glob>`: a `/sys/class/backlight` name (a shell glob) that never drives the built-in panel, such as a Touch Bar's. It is never picked, not even when a later directive or the built-in order names it.
- `backlight-prefer <name>`: the built-in panel's backlight, a literal name, tried after `gmux_backlight` and before the GPU and ACPI ones, in file order.
- `ddc-require-connector-ddc`: the display driver registers no DDC channel, so a probe would only walk unrelated I2C buses. An external monitor (other than an Apple Studio or XDR Display, which `arch-brightness-display-apple` drives with asdcontrol) is probed only when its DRM connector has a `ddc` node (`/sys/class/drm/card*-<connector>/ddc`); otherwise it gets no DDC or backlight control, and the built-in panel is never dimmed in its place.

No environment variable moves the file: these commands also run under `sudo` and from the brightness keys. Their tests (`tests/shell.d/hw-display-test.sh`, `tests/shell.d/brightness-display-test.sh`) run a copy rewritten to read a fixture in its place.

#### Fingerprint readers (`fingerprint-readers`)

`arch-hw-fingerprint` finds USB readers by their product string or vendor. A reader the kernel drives some other way (a Mac's Touch ID sensor, behind its Secure Enclave) is named by the platform package in `/usr/share/arch-platform/fingerprint-readers`; Arch ships none. Each line is an absolute path, a shell glob, then the value that file reads once the reader is usable; the reader is present when any file the glob matches reads that value. The value must be the file's whole content, not part of it (Touch ID reads `not-ready` before it reads `ready`). Three details decide a match: the file's trailing newlines are dropped before comparing (sysfs ends every value with one), fields are split on whitespace (so neither the glob nor the value can contain a space), and the file is read as the user running the check, the session user, so it must be readable by that user and not only by root. Blank lines, whole-line `#` comments, relative paths and lines with a missing or extra word are ignored. A platform file never hides a USB reader: when no platform-named file matches, the USB scan still runs. On Apple Silicon, arch-mac names `/sys/bus/platform/drivers/apple_sep/*/diag/touchid ready`. That file is `0444 root:root`, so the session user can read it. The line follows the kernel's names for the Secure Enclave driver (`apple_sep`) and its `diag/touchid` attribute: if a kernel renames either, the reader and the first-run invitation quietly stop appearing, so the platform package changes the line along with its kernel.

The rest of the fingerprint path is the same for every reader: the setup's first-run invitation follows `arch-hw-fingerprint`, so it reaches a machine once its platform's reader is usable, and `arch-setup-security-fingerprint` installs `libfprint-git`. Setup can only enroll a platform's reader once that package carries its driver; for a Mac's Touch ID that is the aarch64 build from omacom/arch-pkgs#806. `tests/shell.d/hw-fingerprint-test.sh` runs a copy rewritten to read a fixture in place of the file.

#### Audio hints (`audio.json`)

The audio panel lists every output, input and playback stream PipeWire has, and the microphone widget counts every recording as the microphone in use (the shell's own level meters never count). A platform whose audio runs through its own processing (DSP filter graphs in front of raw devices, say) has nodes that are neither devices nor apps, and its platform package names them in `/usr/share/arch-platform/audio.json`; Arch ships none, and without it nothing is left out.

```json
{
  "hidden": ["<pattern>", "..."],
  "replaced": [{ "node": "<pattern>", "by": "<pattern>" }]
}
```

A pattern is a JavaScript regular expression matched against a whole `node.name`. A `hidden` node is never listed as an output, an input or an app stream, unless it is the current default output or input (so the panel always shows what's in use), and never lights the microphone widget; a `replaced` node is left out only while a node matching `by` exists (a mono processed microphone behind a stereo copy of it, say). Missing or malformed JSON means no hints, and an invalid pattern or entry is skipped. The shell reads the file at that fixed path, which no environment variable moves (`src/shell/Commons/AudioNodes.qml`), and `tests/shell.d/audio-test.sh` covers the parsing.

A virtual source (an `Audio/Source/Virtual`, such as EasyEffects' or a platform's microphone mapping) needs no hint: Quickshell leaves it untyped, so the panel and widget set its volume and mute through `wpctl` (`src/shell/Commons/UntypedInput.qml`, one `pactl subscribe` for the whole shell), shows no level meter for it (Quickshell's peak monitor takes typed nodes only), and the panel lists it because PulseAudio does (`arch-audio-sink-availability sources`).

### Why `etc-overrides/` exists

Some files under `/etc/` (`.bashrc` in `/etc/skel`, `nsswitch.conf`,
`security/faillock.conf`, `cups/cups-browsed.conf`, `plymouth/plymouthd.conf`)
are owned by upstream Arch packages, so we can't install over them via pacman
without a file conflict. Instead their sources (under `etc/` in the repo;
`.bashrc` from `default/bashrc`) ship at
`/usr/share/arch/etc-overrides/` and the `arch-settings` `post_install`
/ `post_upgrade` scriptlet `cp -f`'s them into place.

Tradeoff: user edits to those files get clobbered on every `arch-settings`
upgrade. This is documented in the PKGBUILD.

## Locate indexing

`default/systemd/system/plocate-updatedb.service.d/10-arch.conf` ships through `arch-settings` to `/usr/lib/systemd/system/plocate-updatedb.service.d/10-arch.conf`. It replaces the existing service's `ExecStart` with `updatedb --prune-bind-mounts=no --add-prunepaths=/.snapshots`, keeping Btrfs subvolume mounts searchable and excluding Snapper snapshots. The upstream service retains its timer, resource limits, and sandbox; Arch's existing AC-power condition still applies.

`/etc/updatedb.conf` remains owned by plocate and is never rewritten by Arch. The command-line options override bind-mount pruning and add to the administrator's existing path exclusions. Installer and AUR package refreshes pass the same options directly because installation may run without systemd and an explicitly requested refresh should work on battery.

Arch's systemd package hook reloads units when the vendor drop-in is installed or upgraded. The settings package containing the drop-in must ship alongside the runtime package that removes the old configuration helper and migration. Pacman removes those retired files; no new state migration is needed. A running indexer finishes with its original options, and subsequent service starts use the drop-in. For an immediate local test after installing the packages, restart `plocate-updatedb.service` while connected to AC power.

## Env bootstrap (`default/bash/env-bootstrap`)

Single source of truth for `ARCH_PATH` and dev-link-aware `PATH`. It:

- Sources `/etc/arch.conf` (written by `arch-dev-link`, reset to the
  package path by `arch-dev-unlink`) if present; otherwise forces
  `ARCH_PATH=/usr/share/arch` so a stale inherited value can't survive
  an `arch-dev-unlink`.
- Prepends `$ARCH_PATH/src/cli` to `PATH` **only when** `ARCH_PATH` is
  not `/usr/share/arch`. On a production install the binaries are
  already on `PATH` as `/usr/bin/arch-*` via the `arch` package.
- Prepends mise's `command-wrappers/bin` so subscription account dispatch runs before inherited tool binaries, then appends `~/.local/share/mise/shims` and `~/.local/bin` so login shells and the uwsm session find mise-managed tools. The existing mise tool shims also dispatch these wrappers for SSH commands that run no shell setup; the PAM path needs no additional entry. `etc/mise/conf.d/arch-agent-accounts.toml` declares the Claude, Codex, and Grok wrappers; `mise reshim` builds them during user setup and migration. Each invocation resolves the selected account through `arch-agent-account-exec`, while an explicit provider home takes precedence. Credentials and running sessions remain in their original account homes.

Sourced by every entry point that needs the env set:

```
/etc/profile.d/arch.sh                      (system login shells)
/etc/skel/.bashrc                              (interactive shells)
/usr/share/uwsm/env.d/10-arch               (Hyprland session via uwsm)
/usr/share/arch/default/bash/envs           (SSH / non-login bash)
```

Idempotent — safe to source more than once in the same shell.

`PATH` covers everything the user runs, but not `sudo`, which resolves command
names against `secure_path` from `/etc/sudoers`. So `arch-dev-link` also
writes `/etc/sudoers.d/arch-dev-path`:

```
Defaults secure_path="<checkout>/bin:/usr/local/sbin:/usr/local/bin:/usr/bin"
```

Without it, `sudo arch-*` fails for a command the package has not shipped
yet and silently runs the packaged copy of one it has. The drop-in is validated
with `visudo -c` before install and removed by `arch-dev-unlink`; unlike
`/etc/arch.conf`, it takes effect without a reboot.

Factory reset is an exception: it always self-elevates through `/usr/bin/arch-system-factory-reset` and refuses a checkout copy that differs from the installed command, including when invoked with `sudo`. Install the matching package before resetting so a newer checkout cannot silently hand off to older account-scrubbing code.

## Runtime finalization (`arch-provision-user`)

Runs once per user. It does **not** copy `~/.config/**`, `~/.bashrc`,
`flags.lua`, or the nautilus extensions — `/etc/skel` already seeded those.
It only does the things `/etc/skel` can't:

- Skill symlinks into `~/.agents/skills/<name>`, `~/.claude/skills/<name>`, `~/.codex/skills/<name>`, `~/.pi/agent/skills/<name>`, `~/.gemini/config/skills/<name>` (Antigravity), `~/.hermes/skills/<name>`, and each existing `~/.hermes/profiles/*/skills/<name>` → `$ARCH_PATH/default/agents/skills/<name>`, looping over every skill directory there (currently `arch` and `diagnose-crash`) so new skills need no edit. Symlinks (not copies) so `arch dev link` against a dev checkout repoints them correctly. Hermes profile dirs are only linked when they already exist — provision does not create Hermes profiles.
- `xdg-user-dirs-update` (Templates/Public/Desktop folded back into `$HOME`)
  and `~/.config/gtk-3.0/bookmarks` (needs `$HOME` expansion).
- Hyprland's package-owned default input reads `XKBLAYOUT` / `XKBVARIANT`
  from `/etc/vconsole.conf`; no per-user Hyprland config rewrite is needed.
- `xdg-settings set default-web-browser chromium.desktop` and
  `xdg-mime default HEY.desktop x-scheme-handler/mailto` (XDG-aware paths).
- `arch-refresh-applications` (composes generated `.desktop` launchers).
- Sources `installer/user/all.sh` — theme, chromium, git, xcompose, mise,
  keyring, per-user hardware quirks (asus mic/mixer, framework f13 audio, …).
- On `--first-install`, marks every shipped user migration as already applied
  for the freshly-created user.

Idempotency marker: `~/.local/state/arch/done/finalize-user`, managed
by `arch-done`.

The ISO calls it as `arch-provision-user --force --first-install` in the
target chroot as the install user, after `arch-apply-system` has finished
the root-side work. `arch-provision-owner` makes the same call (with
`ARCH_SETUP_CONTEXT=provision-owner`) when it creates the user during
deferred first-boot provisioning.

## Migrations (`arch-migrate`)

See [`migrations.md`](../agents/skills/migrations.md) for the full migration model, authoring
guidelines, and troubleshooting notes.

Arch migrations live in `migrations/*.sh` and run per-user through
`arch-migrate`. Completion state lives in
`~/.local/state/arch/migrations/`, so every user gets a chance to run every
migration. Migrations run as the user; privileged work should invoke the
appropriate helper or privilege prompt. Migrations must be idempotent;
machine-wide repairs should no-op when another user already applied them.

Each graphical user has `arch-migrate-notify.service`, started once per login
through `WantedBy=graphical-session.target` and ordered after that target so
notification actions can safely launch through UWSM. The `arch-pkgs`
PKGBUILD has shipped `arch-update-user-notify.service` as a symlink onto
it, so users enabled under the old unit name keep working before they reach
migration `1785095882`.
It runs `arch-migrate-notify` as
that user, which checks `arch-migrate --pending`. If this user has missing
migration state, it shows a notification that opens a terminal for
`arch-migrate`. The notifier never runs migrations in the background.

Login is the only trigger. Nothing watches the packaged migration directory: a
watcher cannot tell a bypassed `pacman -Syu` from the package transaction inside
a normal `archctl update`, so it notified about migrations that `arch-migrate`
was already applying in the visible update terminal.

`arch-migrate` waits for any active pacman transaction to finish, then runs
pending migrations. It does not need `--force`; migrations happen when state
files are missing. `archctl update` runs `arch-migrate` after the package
transaction in the already-visible update terminal, then runs
`arch-hook post-update`.

## First-run (`arch-provision-first-run`)

Runs once on first interactive login, after the user manager is live. It
first runs `arch-provision-user || true` so finalize catches up if it
never ran, then handles the steps that need a running graphical session
and/or a working user systemd instance:

- `arch-hook-install post-update` for the two shipped hooks
  (`setup-fingerprint.hook`, `setup-agent.hook`).
- `installer/user/first-run/enable-user-units.sh` — daemon-reload, then
  `systemctl --user enable --now` the shipped user units (`bt-agent`,
  `arch-sleep-lock`, `arch-recover-internal-monitor`,
  `arch-migrate-notify.service`, `arch-fcitx5.service`,
  `arch-crash-watch.service`) so they run in the first session too.
  Done here, not at finalize, because
  the user manager isn't reachable from the ISO chroot; `ConditionPath*`
  in the unit files keeps services inert when they don't apply.
- `arch-lifecycle-dispatch setup-user` — the platform's own user setup,
  now with the session up (a no-op where the platform registers none; see
  [lifecycle-dispatch.md](lifecycle-dispatch.md)).
- `installer/user/first-run/gnome-theme.sh`,
  `installer/user/first-run/gtk-primary-paste.sh` — GNOME/GTK settings that
  need the dconf daemon.
- `installer/user/first-run/audio-tuning.sh` — apply speaker tuning.
- `installer/user/first-run/welcome.sh` — keybindings toast that greets the
  first login and opens the cheatsheet when clicked. The caller runs
  `arch-notification-wait` once before this and the Wi-Fi step, so both
  toasts land on a live notification server.
- `installer/user/first-run/wifi.sh` — Wi-Fi/update toasts (waits detached on
  `nm-online` so the update prompt only lands once there is a connection).

The entire sequence has one idempotency marker:
`~/.local/state/arch/done/first-run-user`, managed by `arch-done`.
Completed users exit before any first-run step. On failure the marker is not
written and the sequence retries next login.

Completion markers live under `~/.local/state/arch/done/`. Use
`arch-done check <name>` to check one and `arch-done mark <name>` to record it.
Use `arch-done ensure <name>` as a conditional when the guarded work should
run only once; it records completion before returning success.
The Quattro upgrade completes graphical first-run for upgraded users and moves
the legacy finalization marker from `~/.local/state/arch/` into `done/`.

## Root-side install orchestration

`arch-apply-system` (root, in chroot) runs target-side setup at ISO
finalization. It sources:

- `installer/config/all.sh` — theme links, lockout limits, lockscreen PAM,
  powerprofilesctl shebang fix, SSH command path and keepalive, docker setup,
  Snapper retention, locate index tuning, service enablement, firewall.
- `installer/hardware/all.sh` via `arch-apply-hardware` — vendor- and
  device-specific kernel modules, udev rules, microcode, wireless regdom,
  ASUS / Framework / Intel / Apple / Lenovo quirks.
- `installer/login/all.sh` — SDDM theme/session config.
- `installer/post-install/all.sh` — final pacman/udev/localdb passes.

Logging goes to `/var/log/arch-install.log` via
`installer/helpers/logging.sh`.

Platform-specific setup asks `arch-hw-platform`, which prints `x86`, `aarch64`, `aarch64-apple`, `aarch64-qualcomm`, `aarch64-n1x` or `aarch64-gb10` (the naming standard is in AGENTS.md under Platforms). It reads the vendor prefix of each token in the device tree's root `compatible` (`apple,` or `qcom,`, from `/proc/device-tree` or `/sys/firmware/devicetree/base`) and the CPU architecture, and fails when they contradict each other. A Snapdragon laptop's `qcom,` tree is `aarch64-qualcomm`. The NVIDIA N1x boots with ACPI and no device tree; it is `aarch64-n1x` when its MediaTek I2C controllers (ACPI `NVDA0200`) or its GPU (PCI `10de:2e06`) are present, and a device tree naming Apple or Qualcomm alongside them is a contradiction. An NVIDIA GB10 desktop, such as the DGX Spark, also boots with ACPI; it is `aarch64-gb10` when its GPU (PCI `10de:2e12`) is present, with the same contradictions, and an N1x signature alongside it is one too. A manifest written by an older image builder may still say `apple-silicon`, `generic-aarch64`, `generic` or `qualcomm`, which read as `aarch64-apple`, `aarch64`, `x86` and `aarch64-qualcomm`.

An image built away from the machine it will run on names its target in a root-owned manifest, `/var/lib/arch/image/target` (`format=1`, `platform=<arch-hw-platform value>`, unknown keys ignored). While the root is being built rather than booted, the detector answers from the manifest and never reads the build host's device tree. The root counts as built when it shows it: no `/run/systemd/system`, PID 1's root is another one (a chroot), or PID 1 is not systemd (a PID namespace). A booted system always answers from its hardware, even with a manifest left behind, so no unit that asks the detector may use `PrivatePIDs=`. As root the detector restarts in an empty environment and ignores the fixture variables its tests use.

The package lists the ISO pacstraps live at `installer/arch-base.packages`
and `installer/arch-other.packages`; the ISO builder also reads them when
constructing its offline mirror.

A platform's default package set is the base list, then its architecture's additions, then its own: `installer/arch-aarch64.packages` on every aarch64 platform, then `installer/arch-<platform>.packages` when that platform has one (`installer/arch-aarch64-apple.packages` on Apple Silicon, `installer/arch-aarch64-qualcomm.packages` on Snapdragon, `installer/arch-aarch64-n1x.packages` on the N1x, `installer/arch-aarch64-gb10.packages` on the GB10). x86 installs the base list alone. `arch-pkg-defaults [platform]` prints the composed set, for the running machine by default (via `arch-hw-platform`, so an image build gets its target's set), and `arch-reinstall-pkgs` installs it.

## Platform display hints (`/usr/share/arch-platform/displays.conf`)

`arch-hw-display` picks the built-in panel's backlight by name (`gmux_backlight`, then `amdgpu_bl*`, `intel_backlight`, `acpi_video*`, else the first one listed, never a T2 Touch Bar's `appletb_backlight`), and `arch-brightness-display` probes every external monitor over DDC. Where a platform's names or display driver differ, its platform package says so in `/usr/share/arch-platform/displays.conf`; Arch ships none, and without it both behave as above. One directive per line, whitespace-separated; blank lines, whole-line `#` comments, unknown directives, and lines with a wrong word count or a name that is `.`, `..` or has a `/` are ignored:

- `backlight-skip <glob>`: a `/sys/class/backlight` name (a shell glob) that never drives the built-in panel, such as a Touch Bar's. It is never picked, not even when a later directive or the built-in order names it.
- `backlight-prefer <name>`: the built-in panel's backlight, a literal name, tried after `gmux_backlight` and before the GPU and ACPI ones, in file order.
- `ddc-require-connector-ddc`: the display driver registers no DDC channel, so a probe would only walk unrelated I2C buses. An external monitor (other than an Apple Studio or XDR Display, which `arch-brightness-display-apple` drives with asdcontrol) is probed only when its DRM connector has a `ddc` node (`/sys/class/drm/card*-<connector>/ddc`); otherwise it gets no DDC or backlight control, and the built-in panel is never dimmed in its place.

No environment variable moves the file: these commands also run under `sudo` and from the brightness keys. Their tests (`tests/shell.d/hw-display-test.sh`, `tests/shell.d/brightness-display-test.sh`) run a copy rewritten to read a fixture in its place.

## Explicit resync (`arch-reinstall-configs`)

When an existing user wants to reset to shipped defaults:

```
~/  ←  cp -af /etc/skel/.
```

Replaying `/etc/skel` over `$HOME` is exactly what `useradd -m` does for a
brand-new user, so this one copy resyncs `.bashrc`, `.config/**`,
`.local/share/applications/`, the nautilus-python extensions, hypr toggles,
branding files, and the shipped migration markers in a single pass.

Then it runs `arch-refresh-limine`, `arch-refresh-plymouth`, and the
nvim refresh. Destructive: existing user files copied from `/etc/skel` are
clobbered without backup. Fastfetch is package-owned at
`/etc/fastfetch/config.jsonc`; delete `~/.config/fastfetch/config.jsonc` to
return to the packaged default.

## Quick reference: where does X live?

| Goal | Touch |
| --- | --- |
| Default file at `~/.config/foo/` | `config/foo/` |
| `/etc/` drop-in we own outright | `etc/` |
| `/etc/` file owned by an upstream package | `etc/` (see `etc/security/faillock.conf`), then add to `etc-overrides` in `arch-settings` PKGBUILD + scriptlet |
| Package-owned system file (e.g. systemd user service in `/usr/lib`) | `default/`, then add the `install -Dm644` line in `arch-settings` PKGBUILD |
| Per-user file that's static but lives outside `~/.config` | `default/`, then add `install -Dm644 ... $pkgdir/etc/skel/...` in `arch-settings` PKGBUILD |
| Runtime tweak that needs `$HOME` or live system state | extend `arch-provision-user`, or add a per-user leaf under `installer/user/` and wire into `installer/user/all.sh` |
| One-time root-side setup step | `installer/config/*.sh` or `installer/hardware/*.sh`, wire into `installer/config/all.sh` or `installer/hardware/all.sh` |
| One-time fix for existing installs | `migrations/<unix-timestamp>.sh` |
| Package-owned path something else may already write | Prefer a path nothing else writes, such as a vendor drop-in under `/usr/lib`. Otherwise the `--overwrite` entry in `src/cli/arch-update-system-pkgs` has to ship a release before the file |
| User-facing `arch-*` command | `src/cli/arch-<group>-<verb>` — see `GROUP_DESCRIPTIONS` in `src/cli/archctl` |
| New stock theme | `themes/<name>/` (+ matching templates under `default/themed/` if they need theme colors) |
| User-installed theme | `~/.config/arch/themes/<name>/` |
| Generated current theme/background state | `~/.local/state/arch/current/` |

## Kitty defaults and user overrides

Kitty loads `/etc/xdg/kitty/kitty.conf` before `~/.config/kitty/kitty.conf`. The `arch-settings` package owns the system file; the user template contains only the active theme include and commented examples for personal overrides. Keeping the theme include in the user file lets users remove it without changing the packaged defaults. Individual inherited keybindings can be unmapped with an empty `map <shortcut>` directive, or all inherited bindings can be cleared with `clear_all_shortcuts yes`.

The system default uses `allow_remote_control socket-only` so Arch can query the active terminal directory over its Unix socket while Kitty rejects remote-control requests arriving through terminal output. Changing this setting requires restarting Kitty. The migration refreshes the exact previous stock config with a backup; customized configs retain their settings and ordering, with only explicit unrestricted `yes`, `y`, or `true` remote-control settings commented out.
