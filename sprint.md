# Sprint

## Integrated pull requests

| PR | Change |
| --- | --- |
| #481 | Improve tiling and top bar defaults |
| #482 | Trim default apps and remove RetroArch |
| #484 | Add build, CI, and security checks |
| #485 | Fix downloads when `/tmp` is full |
| #486 | Type all shipped Python sources |
| #487 | Group application source under `arch` |
| #488 | Add an Arch branded cursor theme |
| #489 | Remove the preinstalls bundle |
| #490 | Rename internal `arch_path` variable to `ap` |
| #491 | Raise the `/tmp` tmpfs limit |
| #492 | Use `AP` as the session root variable |
| #493 | Add default engineering and desktop guidance |
| #494 | Restore Cosmic icons and capture its preview |
| #495 | Use the Braille Arch mark in Fastfetch |
| #496 | Remove passwordless sudo grants |
| #497 | Remove sudoless Docker option |
| #499 | Remove model-specific hardware integrations |
| #504 | Add verified ISO download, checksum, and assembly tooling |
| #505 | Add repository consolidation roadmap |
| #506 | Show scroll position in overflowing menus |
| #507 | Use scrolling and tiling as the public workspace modes |
| #508 | Refresh the battery glyph from UPower state changes |
| #509 | Set a useful default size for Disktree |
| #510 | Add the Python-rendered ArchISO profile |
| #512 | Build Arch ISO releases in CI |
| #513 | Pass the runner architecture into ISO builds |
| #514 | Build ArchISO with scoped container privileges |
| #515 | Pass CI environment into the ISO container |
| #516 | Mount ISO build directories separately |
| #517 | Resolve ISO mount sources on the host |
| #518 | Isolate the ISO build mount namespace |
| #519 | Use an isolated PID namespace for ISO builds |
| #520 | Isolate ISO build mount and PID namespaces |
| #521 | Keep inherited mount propagation in the ISO namespace |
| #522 | Run ISO builds as an unprivileged user |
| #523 | Bind the container proc filesystem into ArchISO chroots |
| #524 | Allow isolated ArchISO mounts under AppArmor |
| #525 | Load the AppArmor policy from standard input |
| #526 | Publish complete ArchISO images with release parts |
| #527 | Use a signed ARMv8 repository for ISO builds |
| #528 | Update roadmap with integrated sprint state |
| #529 | Remove duplicate ISO error settings |
| #530 | Count active ISO mirror directives |
| #531 | Validate relative ISO profile key paths |
| #532 | Tile and maximize Disktree windows |
| #533 | Keep ArchISO worktree inside container |
| #534 | Allow fchmodat2 in ArchISO container seccomp |
| #535 | Build ARM GRUB without unavailable AT module |
| #536 | Keep the charging indicator for slow charging |
| #537 | Filter ARM GRUB modules by package availability |
| #538 | Remove CLI wrappers backed by Python modules |
| #539 | Remove Windows VM from the desktop menu |
| #541 | Migrate another set of CLI wrappers |
| #542 | Move default app rules into user YAML |
| #544 | Show charging glyph from device state |
| #545 | Migrate NVIDIA hardware command to Python |
| #546 | Record CLI hardware migration |
| #547 | Migrate clamshell hardware command to Python |
| #548 | Migrate Intel hardware predicates to Python |
| #549 | Migrate Vulkan and touchscreen hardware commands to Python |
| #550 | Migrate external monitor detection to Python |
| #551 | Migrate NVIDIA GSP checks to Python |
| #552 | Migrate hybrid GPU detection to Python |
| #553 | Migrate NVIDIA display detection to Python |
| #554 | Configure Disktree window for Hyprland |
| #555 | Keep Disktree in the active workspace layout |
| #556 | Migrate laptop detection to Python |
| #557 | Migrate DMI hardware matching to Python |
| #558 | Migrate device tree hardware matching to Python |
| #559 | Migrate touchpad detection to Python |
| #560 | Supervise the Arch desktop shell |
| #561 | Migrate fingerprint detection to Python |
| #562 | Migrate backlight detection to Python |
| #563 | Migrate monitor recovery to Python |
| #564 | Migrate current workspace layout command to Python |
| #565 | Migrate Apple monitor predicate to Python |
| #566 | Migrate modeless monitor recovery query to Python |
| #567 | Migrate active external monitor check to Python |
| #568 | Migrate default dictation command to Python |
| #569 | Migrate default terminal command to Python |
| #570 | Migrate default editor command to Python |
| #571 | Migrate default browser command to Python |
| #572 | Split ISO release images into multiple parts |
| #573 | Migrate application restart commands to Python |
| #574 | Migrate notification time command to Python |
| #575 | Migrate notification dismiss command to Python |
| #576 | Preserve notification dismiss usage output |
| #577 | Migrate weather notification command to Python |
| #578 | Migrate battery notification command to Python |
| #579 | Migrate notification sender to Python |
| #580 | Migrate hibernation availability check to Python |
| #581 | Migrate power profile listing to Python |
| #582 | Migrate Hyprland session lock check to Python |
| #583 | Migrate power profile selection to Python |

PR #483 was closed when its base branch was deleted during integration. Its change was rebased and merged as PR #499.
| #584 | Keep a themed desktop visible during shell recovery |
| #585 | Migrate clipboard and emoji menu launchers to Python |
| #586 | Migrate Files launchers to Python |
| #587 | Migrate terminal tmux launcher to Python |
