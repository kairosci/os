#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const fs = require('fs')

const utilQml = fs.readFileSync(path.join(root, 'src/arch/shell/Commons/Util.qml'), 'utf8')
const mediaQml = fs.readFileSync(path.join(root, 'src/arch/shell/Ui/BackgroundMedia.qml'), 'utf8')
const backgroundQml = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/background/Background.qml'), 'utf8')
const lockQml = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/lock/LockView.qml'), 'utf8')
const lockVideoQml = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/lock/LockVideoSurface.qml'), 'utf8')
const videoQml = fs.readFileSync(path.join(root, 'src/arch/shell/Ui/BackgroundVideo.qml'), 'utf8')
const themeSwitcher = fs.readFileSync(path.join(root, 'src/arch/commands/arch-theme-switcher'), 'utf8')
const quattroUpgrade = fs.readFileSync(path.join(root, 'src/arch/commands/arch-upgrade-to-quattro'), 'utf8')
const barTextColor = fs.readFileSync(path.join(root, 'src/arch/commands/arch-bar-text-color'), 'utf8')
const menuImages = fs.readFileSync(path.join(root, 'src/arch/commands/arch-menu-images'), 'utf8')
const lockService = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/lock/Service.qml'), 'utf8')
const lockPoster = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/lock/poster.py'), 'utf8')
const lockPosterConfig = fs.readFileSync(path.join(root, 'data/shell/lock-poster.yml'), 'utf8')
const batteryService = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/services/battery/Service.qml'), 'utf8')
const themeSet = fs.readFileSync(path.join(root, 'src/arch/commands/arch-theme-set'), 'utf8')
const directImageList = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/image-picker/list.py'), 'utf8')
const imagePickerConfig = fs.readFileSync(path.join(root, 'data/shell/image-picker.yml'), 'utf8')

assert(
  /function isVideoPath\(path\)[\s\S]*\.test\(String\(path \|\| ""\)\)/.test(utilQml) &&
    !utilQml.includes('split(/[?#]/)'),
  'shared media helper identifies video paths without truncating valid local names'
)
assert(
  fs.existsSync(path.join(root, 'src/arch/shell/Ui/BackgroundVideo.qml')) &&
    /^import QtMultimedia$/m.test(videoQml) && videoQml.includes('MediaPlayer {') && videoQml.includes('VideoOutput {'),
  'the shell has a first-party Qt Multimedia player for video backgrounds'
)
assert(
  /imageUrl: path && !Util\.isVideoPath\(path\) \? Util\.fileUrl\(path\)/.test(mediaQml) &&
    /active: root\.path !== "" && !root\.video/.test(mediaQml) &&
    mediaQml.includes('videoUrl') && mediaQml.includes('videoLoader') &&
    mediaQml.includes('property bool playbackEnabled'),
  'background media loads still images and native video with a shared playback control'
)
assert(
  !lockVideoQml.includes('import Owe') &&
    lockVideoQml.includes('BackgroundMedia {') &&
    lockVideoQml.includes('property string mediaPath') &&
    lockQml.includes('source: "LockVideoSurface.qml"') &&
    lockQml.includes('active: root.videoActive') &&
    /videoActive: root\.video && root\.loadBackground && !root\.displaysBlank && !root\.powerSaverActive/.test(lockQml),
  'the lock screen plays video through its first-party player and releases it when hidden'
)
assert(
  lockService.includes('poster.py') && lockPoster.includes('acquire_lock') &&
    lockPoster.includes('make_poster') && lockPosterConfig.includes('timeout_seconds: 5'),
  'the lock poster uses a bounded Python converter with a shared cache lock'
)
assert(
  /^\s*import QtMultimedia/m.test(videoQml) &&
    videoQml.includes('audioOutput: audioLoader.item') &&
    lockVideoQml.includes('audioEnabled: false'),
  'native wallpaper audio is controlled per output and stays off on the lock screen'
)
assert(
  !lockQml.includes('import Owe'),
  'the lock view itself carries no foreign import, so the lock still loads without the feed module'
)
assert(
  lockQml.includes('path: root.loadBackground ? (root.video ? root.videoPosterPath : root.backgroundPath) : ""') &&
    lockQml.indexOf('id: videoLoader') > lockQml.indexOf('MultiEffect {') &&
    lockQml.includes('visible: root.video') &&
    !lockQml.includes('wallpaper.video'),
  'the lock screen keeps its poster fallback and image effect while native video plays'
)
assert(
  !mediaQml.includes('mipmap'),
  'the shared image path leaves mipmapping off, as the desktop background had it'
)
assert(
  /instant \|\| !displayedBackground \|\| isVideo\(path\) \|\| isVideo\(displayedBackground\)[\s\S]*displayedBackground = finalPath/.test(backgroundQml),
  'video switches bypass the image-only reveal stack and use the durable background path'
)
assert(backgroundQml.includes('BackgroundMedia {') && lockQml.includes('BackgroundMedia {'), 'desktop and lock screen share still rendering')
assert(
  backgroundQml.includes('playbackEnabled: !root.sessionObscured') &&
    backgroundQml.includes('displayedReloads') && mediaQml.includes('property int reloads'),
  'the desktop handles video backgrounds directly and reloads replaced media'
)
assert(
  backgroundQml.includes('sessionObscured') && backgroundQml.includes('fullscreenHere') &&
    backgroundQml.includes('Hyprland.monitorFor') && backgroundQml.includes('arch.lock') &&
    backgroundQml.includes('arch.battery'),
  'native desktop video pauses behind locks, screensavers, fullscreen windows and power saver'
)
assert(
  barTextColor.includes('magick "$background_path[0]"'),
  'bar colour sampling reads one frame instead of decoding a whole video'
)
assert(
  menuImages.includes('pending_video_file') && /video_jobs=\$\(\( \$\(nproc\) \/ 4 \)\)/.test(menuImages),
  'video thumbnails fan out narrower than single-threaded vips jobs'
)
assert(
  themeSwitcher.includes('fast_signature="v2"'),
  'the theme preview cache rebuilds after preview discovery learned about video'
)
assert(
  /lazy_thumbnails == true && \$cache_only != true \]\] && ! is_video_path/.test(menuImages),
  'a video never stands in as its own lazy thumbnail, so the fan out cap always applies'
)
assert(
  /thumbnail_command=\(timeout -k \d+ \d+ ffmpegthumbnailer/.test(menuImages),
  'a stalled video cannot hold the picker shut, because its generator is time bounded'
)
assert(
  directImageList.includes('make_video_thumbnail') &&
    directImageList.includes('subprocess.Popen(command') &&
    directImageList.includes('if not thumbnail.is_file() and not is_video(image, config)') &&
    imagePickerConfig.includes('timeout_seconds: 10') && imagePickerConfig.includes('generator: ffmpegthumbnailer'),
  'a direct picker scan generates bounded video thumbnails without content-hashing the media'
)
assert(
  themeSet.includes('choose_staged_theme_background') &&
    themeSet.includes('background_transition_uses_snapshots') &&
    themeSet.includes('BACKGROUND_TRANSITION_SNAPSHOTS=false') &&
    /if \[\[ \$BACKGROUND_TRANSITION_SNAPSHOTS == "true" \]\]/.test(themeSet) &&
    /if \[\[ -z \$CHOSEN_THEME_BACKGROUND \|\| ! -f \$CHOSEN_THEME_BACKGROUND \]\]/.test(themeSet),
  'theme changes disable both transition snapshots whenever either side is a video'
)
assert(
  /function onScreensChanged\(\) \{[\s\S]*?root\.displaysBlank = false/.test(lockService),
  'a display coming back gives up the blank state instead of freezing a visible wallpaper'
)
assert(
  lockService.includes('function screenBlank(screenName)') &&
    lockService.includes('function applyMonitorDpms(text)') &&
    lockService.includes('command: ["hyprctl", "monitors", "-j"]') &&
    lockService.includes('running: root.locked && root.videoBackground') &&
    /displaysBlank: root\.screenBlank\(lockSurface\.screen/.test(lockService) &&
    /function runWake\(\) \{[\s\S]*?root\.monitorDpmsKnown = false/.test(lockService) &&
    /function runBlank\(\) \{[\s\S]*?root\.monitorDpmsKnown = false/.test(lockService),
  'a locked video wallpaper follows what each panel actually did, not only what the lock asked for'
)
assert(
  /videoActive: root\.video && root\.loadBackground && !root\.displaysBlank && !root\.powerSaverActive/.test(lockQml) &&
    /displaysBlank: root\.screenBlank\(/.test(lockService) &&
    /powerSaverActive: root\.powerSaverActive/.test(lockService) &&
    /function runBlank\(\) \{\s*\n\s*root\.displaysBlank = true/.test(lockService) &&
    /function runWake\(\) \{\s*\n\s*root\.displaysBlank = false/.test(lockService),
  'the native lock player stops once displays go dark or power-saver is active'
)
assert(
  batteryService.includes('property string activePowerProfile') &&
    batteryService.includes('powerSaverOnBattery: BatteryModel.isPowerSaverOnBattery(UPower.onBattery, activePowerProfile)') &&
    /function onProfileChanged\(\) \{\s*root\.powerProfileSignals\+\+\s*root\.activePowerProfile = root\.profileName\(PowerProfiles\.profile\)/.test(batteryService) &&
    batteryService.includes('root.activePowerProfile = BatteryModel.profileAfterRead(root.activePowerProfile, text, root.powerProfileReadSignals, root.powerProfileSignals)') &&
    /if \(powerProfileReadProcess\.running\) \{\s*powerProfileReadPending = true/.test(batteryService) &&
    batteryService.includes('if (root.powerProfileReadPending) Qt.callLater(root.refreshPowerProfile)') &&
    batteryService.includes('case PowerProfile.PowerSaver: return "power-saver"') &&
    batteryService.includes('"get-property", "net.hadess.PowerProfiles", "/net/hadess/PowerProfiles", "net.hadess.PowerProfiles", "ActiveProfile"') &&
    !batteryService.includes('["powerprofilesctl"') &&
    !/Timer \{[^}]*refreshPowerProfile/.test(batteryService) &&
    batteryService.includes('function refreshPowerProfile(): void { root.refreshPowerProfile() }'),
  'the battery service tracks the active power-saver profile'
)
assert(
  themeSwitcher.includes("-iname '*.mp4'") &&
    themeSwitcher.includes('mp4 m4v mov webm mkv avi') &&
    themeSwitcher.includes('preview.mp4'),
  'theme switcher previews video-only themes, named preview files included'
)
assert(quattroUpgrade.includes("-iname '*.mp4'"), 'Quattro upgrade can seed a video-only theme background')
JS

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/bin" "$test_tmp/backgrounds" "$test_tmp/generator-cache" "$test_tmp/direct-cache"
printf 'not a real video\n' >"$test_tmp/backgrounds/sample.mp4"

cat >"$test_tmp/bin/ffmpegthumbnailer" <<'SH'
#!/bin/bash
if [[ -n ${POSTER_CALLS:-} ]]; then
  printf '%s\n' "$*" >>"$POSTER_CALLS"
fi
while (( $# > 0 )); do
  case "$1" in
    -i) input=$2; shift 2 ;;
    -o) output=$2; shift 2 ;;
    *) shift ;;
  esac
done
printf 'thumbnail for %s\n' "$input" >"$output"
SH
chmod +x "$test_tmp/bin/ffmpegthumbnailer"

cat >"$test_tmp/bin/md5sum" <<'SH'
#!/bin/bash
if (( $# > 0 )); then
  printf 'unexpected file hash: %s\n' "$*" >>"$MD5_FILE_CALLS"
fi
exec /usr/bin/md5sum "$@"
SH
chmod +x "$test_tmp/bin/md5sum"

md5_file_calls="$test_tmp/md5-file-calls"
PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$test_tmp/generator-cache" MD5_FILE_CALLS="$md5_file_calls" \
  "$ROOT/src/arch/commands/arch-menu-images" --prepare-only "$test_tmp/backgrounds"

generator_thumbnail=$(find "$test_tmp/generator-cache/arch/image-selector" -maxdepth 1 -type f -name '*.jpg' -print -quit)
[[ -s $generator_thumbnail ]] || fail "menu image generator creates a video thumbnail"

generator_row=$(AP="$ROOT" XDG_CACHE_HOME="$test_tmp/generator-cache" "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$test_tmp/backgrounds")
IFS=$'\t' read -r generator_row_path generator_row_thumbnail <<<"$generator_row"
[[ $generator_row_path == "$test_tmp/backgrounds/sample.mp4" && $generator_row_thumbnail == "$generator_thumbnail" ]] || \
  fail "direct picker consumes the menu image generator thumbnail" "$generator_row"

poster_calls="$test_tmp/poster-calls"
poster_path=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$test_tmp/poster-cache" POSTER_CALLS="$poster_calls" \
  "$ROOT/src/arch/shell/plugins/lock/poster.py" "$test_tmp/backgrounds/sample.mp4")
[[ -s $poster_path ]] || fail "lock poster creates a shared cached video frame"
cached_poster=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$test_tmp/poster-cache" POSTER_CALLS="$poster_calls" \
  "$ROOT/src/arch/shell/plugins/lock/poster.py" "$test_tmp/backgrounds/sample.mp4")
[[ $cached_poster == "$poster_path" && $(wc -l <"$poster_calls") == 1 ]] || fail "lock poster reuses the cached frame"

row=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$test_tmp/direct-cache" MD5_FILE_CALLS="$md5_file_calls" \
  "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$test_tmp/backgrounds")

IFS=$'\t' read -r row_path row_thumbnail <<<"$row"
[[ $row_path == "$test_tmp/backgrounds/sample.mp4" && $row_thumbnail == *.jpg && -s $row_thumbnail ]] || \
  fail "image picker lists videos with their cached thumbnail" "$row"
[[ ! -s $md5_file_calls ]] || fail "direct video scans avoid hashing the complete media file" "$(<"$md5_file_calls")"

failed_backgrounds="$test_tmp/failed-backgrounds"
failed_cache="$test_tmp/failed-cache"
mkdir -p "$failed_backgrounds" "$failed_cache"
printf 'broken video\n' >"$failed_backgrounds/broken.mp4"
cat >"$test_tmp/bin/ffmpegthumbnailer" <<'SH'
#!/bin/bash
exit 1
SH

cached_row=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$test_tmp/direct-cache" MD5_FILE_CALLS="$md5_file_calls" \
  "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$test_tmp/backgrounds")
[[ $cached_row == "$row" ]] || fail "direct picker reuses its cached video thumbnail" "$cached_row"

failed_rows=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$failed_cache" MD5_FILE_CALLS="$md5_file_calls" \
  "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$failed_backgrounds")
[[ -z $failed_rows ]] || fail "direct picker omits a video whose thumbnail fails" "$failed_rows"

failed_marker=$(find "$failed_cache/arch/image-selector" -maxdepth 1 -type f -name '*.failed' -print -quit)
[[ -n $failed_marker ]] || fail "direct picker remembers a video the converter rejected"

thumbnailer_calls="$test_tmp/thumbnailer-calls"
cat >"$test_tmp/bin/ffmpegthumbnailer" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$THUMBNAILER_CALLS"
exit 1
SH

failed_rows=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$failed_cache" THUMBNAILER_CALLS="$thumbnailer_calls" \
  "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$failed_backgrounds")
[[ -z $failed_rows && ! -e $thumbnailer_calls ]] || fail "direct picker skips a rejected video on the next scan" "$(cat "$thumbnailer_calls" 2>/dev/null)"

generator_failed_cache="$test_tmp/generator-failed-cache"
PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$generator_failed_cache" THUMBNAILER_CALLS="$thumbnailer_calls" \
  "$ROOT/src/arch/commands/arch-menu-images" --prepare-only "$failed_backgrounds"
[[ -s $thumbnailer_calls ]] || fail "menu image generator tries a video it has not seen"
generator_marker=$(find "$generator_failed_cache/arch/image-selector" -maxdepth 1 -type f -name '*.failed' -print -quit)
[[ -n $generator_marker ]] || fail "menu image generator remembers a video the converter rejected"
rm -f "$thumbnailer_calls"
PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$generator_failed_cache" THUMBNAILER_CALLS="$thumbnailer_calls" \
  "$ROOT/src/arch/commands/arch-menu-images" --prepare-only "$failed_backgrounds"
[[ ! -e $thumbnailer_calls ]] || fail "menu image generator skips a rejected video on the next open" "$(<"$thumbnailer_calls")"

# A repaired file gets a fresh key, so the old marker no longer applies, and
# the rows are not cached over its absence, so an in-place repair that leaves
# the directory's mtime alone is still noticed.
touch -d '2 minutes' "$failed_backgrounds/broken.mp4"
PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$generator_failed_cache" THUMBNAILER_CALLS="$thumbnailer_calls" \
  "$ROOT/src/arch/commands/arch-menu-images" --prepare-only "$failed_backgrounds"
[[ -s $thumbnailer_calls ]] || fail "menu image generator retries a video that changed since it was rejected"

timeout_backgrounds="$test_tmp/timeout-backgrounds"
timeout_cache="$test_tmp/timeout-cache"
mkdir -p "$timeout_backgrounds"
printf 'slow video\n' >"$timeout_backgrounds/slow.mp4"
cat >"$test_tmp/bin/ffmpegthumbnailer" <<'SH'
#!/bin/bash
exit 124
SH
timeout_rows=$(AP="$ROOT" PATH="$test_tmp/bin:$PATH" XDG_CACHE_HOME="$timeout_cache" \
  "$ROOT/src/arch/shell/plugins/image-picker/list.py" "$timeout_backgrounds")
[[ -z $timeout_rows ]] || fail "direct picker omits a video whose thumbnail timed out" "$timeout_rows"
timeout_marker=$(find "$timeout_cache/arch/image-selector" -maxdepth 1 -type f -name '*.failed' -print -quit)
[[ -z $timeout_marker ]] || fail "a timed out video is left to retry rather than remembered as failed"

if grep -Eq '^(owe|owe-lockfeed)$' "$ROOT/installer/arch-base.packages"; then
  fail "the desktop no longer depends on an external wallpaper engine"
fi
grep -qx 'qt6-multimedia' "$ROOT/installer/arch-base.packages" || fail "native video playback requires Qt Multimedia"
grep -rqs 'import QtMultimedia' "$ROOT/src/arch/shell/Ui/BackgroundVideo.qml" || fail "the first-party player uses Qt Multimedia"

pass "menu image generator creates thumbnails consumed by the picker"
pass "direct picker generates and reuses still thumbnails"
pass "lock poster creates and reuses a cached frame"
pass "direct picker omits videos whose thumbnails cannot be generated"
pass "a rejected video is remembered so it costs nothing on the next open"
pass "a timed out video is left to retry"
pass "a locked video wallpaper follows the panels' real DPMS state"
pass "native Qt Multimedia is installed without the external wallpaper engine"

source <(awk '
  /^(is_video_path|snapshot_background_path|background_transition_uses_snapshots|choose_theme_background|choose_staged_theme_background|set_theme_background)\(\) \{/ { copying=1 }
  copying { print }
  copying && /^}$/ { copying=0 }
' "$ROOT/src/arch/commands/arch-theme-set")

transition_home="$test_tmp/transition-home"
CURRENT_THEME_PATH="$transition_home/.local/state/arch/current/theme"
NEXT_THEME_PATH="$transition_home/.local/state/arch/current/next-theme"
CURRENT_BACKGROUND_LINK="$transition_home/.local/state/arch/current/background"
BACKGROUND_TRANSITION_CACHE="$transition_home/.cache/arch/background-transitions"
THEME_NAME="video-test"
PREVIOUS_THEME_NAME="$THEME_NAME"
HOME="$transition_home"
mkdir -p "$CURRENT_THEME_PATH/backgrounds" "$NEXT_THEME_PATH/backgrounds" "$HOME/.config/arch/backgrounds/$THEME_NAME"
printf 'old image\n' >"$CURRENT_THEME_PATH/backgrounds/old.png"
printf 'old image staged\n' >"$NEXT_THEME_PATH/backgrounds/old.png"
printf 'new video\n' >"$NEXT_THEME_PATH/backgrounds/new.mp4"
ln -s "$CURRENT_THEME_PATH/backgrounds/old.png" "$CURRENT_BACKGROUND_LINK"

choose_staged_theme_background || fail "staged video background is selected before the theme swap"
expected_staged_background="$CURRENT_THEME_PATH/backgrounds/new.mp4"
[[ $CHOSEN_THEME_BACKGROUND == $expected_staged_background ]] || \
  fail "staged background resolves to its durable post-swap path" "$CHOSEN_THEME_BACKGROUND"
if background_transition_uses_snapshots "$CHOSEN_THEME_BACKGROUND"; then
  fail "image to video theme transitions skip snapshots"
fi
background_transition_uses_snapshots "$CURRENT_THEME_PATH/backgrounds/new.png" || \
  fail "image to image theme transitions retain snapshots"

rm "$CURRENT_BACKGROUND_LINK"
printf 'old video\n' >"$CURRENT_THEME_PATH/backgrounds/old.mp4"
ln -s "$CURRENT_THEME_PATH/backgrounds/old.mp4" "$CURRENT_BACKGROUND_LINK"
if background_transition_uses_snapshots "$CURRENT_THEME_PATH/backgrounds/new.png"; then
  fail "video to image theme transitions skip snapshots"
fi

video_snapshot=$(snapshot_background_path "$CURRENT_THEME_PATH/backgrounds/old.mp4" "video")
[[ -z $video_snapshot && ! -e $BACKGROUND_TRANSITION_CACHE ]] || fail "video files are never snapshotted"

CHOSEN_THEME_BACKGROUND="$transition_home/disappeared.mp4"
BACKGROUND_TRANSITION_SNAPSHOTS=false
THEME_BACKGROUND_INTRO=""
OLD_BACKGROUND_SNAPSHOT=""
PREPARED_BACKGROUND=""
PREPARED_BACKGROUND_SNAPSHOT=""
colors_payload=""
shell_payload=""
shell_ipc() { :; }
set_theme_background
[[ -f $CHOSEN_THEME_BACKGROUND && $(readlink "$CURRENT_BACKGROUND_LINK") == "$CHOSEN_THEME_BACKGROUND" ]] || \
  fail "theme changes recover when a preselected background disappears" "$CHOSEN_THEME_BACKGROUND"

pass "theme transitions skip snapshots whenever either side is a video"
pass "theme changes recover from a missing preselected background"
