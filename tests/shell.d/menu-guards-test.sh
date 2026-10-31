#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const menu = requireFromRoot('src/arch/shell/plugins/menu/MenuModel.js')

const items = {
  'setup.default.browser.brave': { id: 'setup.default.browser.brave', when: 'arch-pkg-present brave-bin', checked: '[[ "$(archctl default browser)" == "brave" ]]' },
  'setup.default.browser.zen': { id: 'setup.default.browser.zen', when: 'arch-pkg-present zen-browser-bin', checked: '[[ "$(archctl default browser)" == "zen" ]]' },
  'install.browser.zen': { id: 'install.browser.zen', disabled: 'arch-pkg-present zen-browser-bin' },
  'plain': { id: 'plain', label: 'No guards' }
}
const script = menu.guardScript(items)
const browserSlot = `\${__arch_read_${menu.guardReaders.indexOf('archctl default browser')}}`

assert(
  script.includes('if { arch-pkg-present brave-bin; } >/dev/null 2>&1; then echo setup.default.browser.brave:w:1; else echo setup.default.browser.brave:w:0; fi'),
  'guard script reports a when: as <id>:w:<0|1>'
)
assert(
  script.includes('then echo setup.default.browser.zen:c:1; else echo setup.default.browser.zen:c:0; fi'),
  'guard script reports a checked: as <id>:c:<0|1>'
)
assert(
  script.includes('if { arch-pkg-present zen-browser-bin; } >/dev/null 2>&1; then echo install.browser.zen:d:1; else echo install.browser.zen:d:0; fi'),
  'guard script reports a disabled: as <id>:d:<0|1>'
)
assert(!/\bplain:[wcd]:/.test(script), 'guard script skips items with nothing to evaluate')
assertEqual(menu.guardScript({ plain: items.plain }), '', 'guard script is empty when no item carries a guard')

// The cost the menu is paying is per fork, not per expression, so what makes
// the batch fast is asking each command once however many rows want it.
assertEqual(
  (script.match(/^exec \{__arch_read_fd_\d+\}< <\(archctl default browser /gm) || []).length,
  1,
  'guard script reads a value command once for the whole batch'
)
assert(
  script.includes(`[[ "${browserSlot}" == "brave" ]]`) && !script.includes('"$(archctl default browser)"'),
  'guard script substitutes the captured answer into the expression'
)
assert(
  script.indexOf('__arch_read_') < script.indexOf('if { arch-pkg-present'),
  'guard script captures readers before any guard runs, since $() would trap a lazy memo in its subshell'
)

// Substitution is confined to the plain `$(reader)` form on purpose. A
// function shadowing the name would also catch these, and answer them wrong.
const untouched = menu.guardScript({
  a: { id: 'a', when: 'command -v arch-dns' },
  b: { id: 'b', when: '[[ "$(AP=/usr/share/arch archctl channel current)" == "stable" ]]' },
  c: { id: 'c', when: '(( $(archctl default browser | wc -l) == 1 ))' }
})
assert(
  untouched.includes('command -v arch-dns')
    && untouched.includes('$(AP=/usr/share/arch archctl channel current)')
    && untouched.includes('$(archctl default browser | wc -l)'),
  'guard script leaves every form but the plain substitution to run the real command'
)
assert(
  !/^__arch_read_/m.test(untouched),
  'guard script captures nothing when no guard uses the plain substitution'
)

// Every reader named in the shipped menu has to be listed, or it silently
// keeps forking once per row that reads it.
const fs = require('fs')
const defaultItems = menu.parseMenuJsonc(fs.readFileSync(path.join(root, 'default/arch/arch-menu.jsonc'), 'utf8'))
const guardText = defaultItems.map(item => `${item.when}\n${item.checked}\n${item.disabled}`).join('\n')
const repeated = [...new Set(
  (guardText.match(/\$\(((?:arch-[a-z0-9-]+(?: [a-z0-9-]+)*)|archctl default browser)\)/g) || []).map(match => match.slice(2, -1))
)].filter(command => guardText.split(`$(${command})`).length > 2)
assertDeepEqual(
  repeated.filter(command => !menu.guardReaders.includes(command)),
  [],
  'guard readers cover every command the shipped menu reads from more than one row'
)
JS

prelude() {
  node -e '
    const path = require("path")
    const menu = require(path.join(process.env.ROOT, "src/arch/shell/plugins/menu/MenuModel.js"))
    process.stdout.write(menu.guardScript({ probe: { id: "probe", when: "true" } }))
  ' | command sed '/^__arch_groups=()$/,$d'
}

# The prelude shadows the real commands for the length of the batch, so it has
# to answer exactly as they do -- including for arguments no shipped guard
# passes today, which an extension is free to write tomorrow.
stub_dir=$(mktemp -d)
trap 'rm -rf "$stub_dir"' EXIT

# `pacman -Q` resolves a name through what installed packages provide, so gvim
# answers for vim and bash answers for sh. A set built from `pacman -Qq` alone
# would miss both and offer to install what is already there.
#
# `-Qi` wraps a long list onto indented continuation lines whenever COLUMNS is
# set, so gvim's provides arrive the way a wrapped terminal would emit them.
cat >"$stub_dir/pacman" <<'STUB'
#!/bin/bash
case "$1" in
-Qq)
  printf '%s\n' bash gvim
  ;;
-Qi)
  cat <<'INFO'
Name            : bash
Provides        : sh
Version         : 5.3.0-1
Name            : gvim
Provides        : vim=9.2.0849-1
                  xxd
Version         : 9.2-1
INFO
  ;;
-Q)
  if [[ $2 == "--" ]]; then
    shift 2
  else
    shift
  fi
  for want in "$@"; do
    case "${want%%[<>=]*}" in bash | gvim | sh | vim | xxd) ;; *) exit 1 ;; esac
  done
  ;;
esac
exit 0
STUB
chmod +x "$stub_dir/pacman"
printf '#!/bin/bash\nexit 0\n' >"$stub_dir/gvim"
chmod +x "$stub_dir/gvim"

guard_prelude=$(prelude)

# Arguments reach both sides as argv. Interpolating them into the shadow's
# script text would let `bash>=1` parse as a redirection, so the case that
# exists to prove constraints work would quietly test `bash` instead.
assert_helper_agrees() {
  local description="$1" helper="$2" command_path shadow_helper
  local -a route=()
  shift 2

  shadow_helper=$helper
  if [[ $helper == "archctl cmd missing" ]]; then
    command_path="$ARCH_TEST_CLI_BIN/archctl"
    route=(cmd missing)
    shadow_helper=arch-cmd-missing
  elif [[ $helper == "archctl cmd present" ]]; then
    command_path="$ARCH_TEST_CLI_BIN/archctl"
    route=(cmd present)
    shadow_helper=arch-cmd-present
  else
    command_path="$ROOT/src/arch/commands/$helper"
    [[ -x $command_path ]] || command_path="$ARCH_TEST_CLI_BIN/$helper"
  fi

  local real=0 shadowed=0
  AP="$ROOT" PATH="$stub_dir:$ARCH_TEST_CLI_BIN:$PATH" "$command_path" "${route[@]}" "$@" >/dev/null 2>&1 || real=$?
  # No runtime dir, so the stub's set is built fresh rather than read from the
  # machine's stored one (or stored in its place).
  XDG_RUNTIME_DIR="" PATH="$stub_dir:$PATH" bash -c "$guard_prelude"$'\n'"$shadow_helper \"\$@\"" "$shadow_helper" "$@" >/dev/null 2>&1 || shadowed=$?
  ((real == shadowed)) || fail "$description" "$helper $*: real=$real shadowed=$shadowed"
}

# vim, sh and xxd are provided rather than installed, and xxd only appears on a
# wrapped continuation line; bash>=1 is a version constraint no set can answer.
pkg_cases=("bash" "vim" "sh" "xxd" "absent" "bash vim" "bash absent" "bash>=1" "vim>=1" "")
for helper in arch-pkg-present arch-pkg-missing; do
  for case in "${pkg_cases[@]}"; do
    read -r -a argv <<<"$case"
    assert_helper_agrees "guard prelude resolves packages as pacman does" "$helper" "${argv[@]}"
  done
done
pass "guard prelude resolves packages through provides, wrapping, and constraints as pacman does"

# Command presence means an executable found through PATH, as shutil.which
# does in the Python command. Shell builtins such as cd are not executables.
cmd_cases=("gvim" "cd" "absent" "gvim absent" "gvim cd" "")
for helper in "archctl cmd present" "archctl cmd missing"; do
  for case in "${cmd_cases[@]}"; do
    read -r -a argv <<<"$case"
    assert_helper_agrees "guard prelude resolves commands as the real helper does" "$helper" "${argv[@]}"
  done
done
pass "guard prelude resolves executable commands as the routed presence commands do"

# A reader is replaced by what it printed, which has to compare identically to
# the substitution it stood in for -- including the trailing newline $() drops.
reader_script=$(node -e '
  const path = require("path")
  const menu = require(path.join(process.env.ROOT, "src/arch/shell/plugins/menu/MenuModel.js"))
  process.stdout.write(menu.guardScript({
    hit: { id: "hit", checked: "[[ \"$(arch-dns)\" == \"Cloudflare\" ]]" },
    miss: { id: "miss", checked: "[[ \"$(arch-dns)\" == \"Google\" ]]" }
  }))
')
reader_result=$(XDG_RUNTIME_DIR="" bash -c '
arch-dns() { printf "Cloudflare\n"; }
export -f arch-dns
'"$reader_script" | sort)
[[ $reader_result == $'hit:c:1\nmiss:c:0' ]] ||
  fail "guard prelude compares a captured reader as the substitution did" "got: $reader_result"
pass "guard prelude compares a captured reader exactly as the substitution it replaced"

# The batch inherits whatever a login shell left set. A reader that exits
# nonzero must not take the rest of the menu's rows down with it.
errexit_result=$(XDG_RUNTIME_DIR="" bash -e -c '
arch-dns() { printf "Cloudflare\n"; return 3; }
export -f arch-dns
'"$reader_script"'
printf "survived\n"' 2>/dev/null)
# Rows arrive in any order, but only once every group is done.
[[ $(head -n 2 <<<"$errexit_result" | sort) == $'hit:c:1\nmiss:c:0' && $(tail -n 1 <<<"$errexit_result") == "survived" ]] ||
  fail "guard batch survives a failing reader under errexit" "got: $errexit_result"
pass "guard batch survives a reader that exits nonzero under errexit"

cat >"$stub_dir/git" <<'STUB'
#!/bin/bash
: "${GIT_CALLS:=/dev/null}"
{ printf '<%s>' "$@"; printf '\n'; } >>"$GIT_CALLS"
STUB
chmod +x "$stub_dir/git"

themes_home=$(mktemp -d)
trap 'rm -rf "$stub_dir" "$themes_home"' EXIT

# A theme copied by hand has nothing to pull, a symlinked one is someone's
# working copy, and a `.git` file is a worktree living elsewhere.
mkdir -p "$themes_home/missing"
mkdir -p "$themes_home/empty/.config/arch/themes"
mkdir -p "$themes_home/copied/.config/arch/themes/handmade"
mkdir -p "$themes_home/cloned/.config/arch/themes/tokyo-night/.git"
mkdir -p "$themes_home/linked/.config/arch/themes" "$themes_home/checkout/.git"
ln -s "$themes_home/checkout" "$themes_home/linked/.config/arch/themes/in-progress"
mkdir -p "$themes_home/worktree/.config/arch/themes/branch"
printf 'gitdir: /elsewhere\n' >"$themes_home/worktree/.config/arch/themes/branch/.git"

# Which themes get pulled, not just that something did: a name with a space in
# it is the one that goes missing the moment a path is split rather than passed
# whole, and it would still print an Updating: line on its way to the wrong
# directory.
many="$themes_home/many/.config/arch/themes"
mkdir -p "$many/tokyo night/.git" "$many/zen/.git" "$many/handmade"
ln -s "$themes_home/checkout" "$many/in-progress"

listed=$(AP="$ROOT" HOME="$themes_home/many" LC_ALL=C "$ROOT/src/arch/commands/archctl" theme extras)
[[ $listed == "$many/tokyo night"$'\n'"$many/zen" ]] ||
  fail "arch-theme-extras lists every clone and nothing else" "got: $listed"
pass "arch-theme-extras lists every clone and nothing else"

git_calls=$(mktemp)
trap 'rm -rf "$stub_dir" "$themes_home" "$git_calls"' EXIT
AP="$ROOT" HOME="$themes_home/many" LC_ALL=C GIT_CALLS="$git_calls" PATH="$ROOT/src/arch/commands:$stub_dir:$PATH" \
  "$ROOT/src/arch/commands/arch-theme-update" >/dev/null 2>&1
pulled=$(<"$git_calls")
[[ $pulled == "<-C><$many/tokyo night><pull>"$'\n'"<-C><$many/zen><pull>" ]] ||
  fail "arch-theme-update pulls each clone by its whole path" "got: $pulled"
pass "arch-theme-update pulls each clone by its whole path"

# The package set is cached across batches, keyed on the local database
# directory. Each case gets its own runtime dir and database, and a pacman
# that logs every query, so what is checked is when the set gets rebuilt and
# whether a stale one could ever answer.
cache_root=$(mktemp -d)
trap 'rm -rf "$stub_dir" "$themes_home" "$git_calls" "$cache_root"' EXIT

cache_bin="$cache_root/bin"
mkdir -p "$cache_bin"
cat >"$cache_bin/pacman" <<'STUB'
#!/bin/bash
echo "$1" >>"$PACMAN_LOG"
case "$1" in
-Qq)
  ls "$FIXTURE_DB/local" | sed 's/-[^-]*-[^-]*$//'
  ;;
-Qi)
  [[ -z ${PACMAN_QI_FAILS:-} ]] || exit 1
  # A transaction landing while the set is being read.
  case "${PACMAN_DURING_QI:-}" in
  install) mkdir -p "$FIXTURE_DB/local/zen-browser-bin-1.0-1" ;;
  lock) touch "$FIXTURE_DB/db.lck" ;;
  esac
  if [[ -d $FIXTURE_DB/local/gvim-9.2-1 ]]; then
    printf 'Name            : gvim\nProvides        : vim=9.2-1\n'
  fi
  ;;
*)
  exit 1
  ;;
esac
STUB
# pacman.conf's DBPath, which pacman-conf prints with a trailing slash.
cat >"$cache_bin/pacman-conf" <<'STUB'
#!/bin/bash
[[ $1 == "DBPath" ]] || exit 1
echo "$FIXTURE_DB/"
STUB
chmod +x "$cache_bin/pacman" "$cache_bin/pacman-conf"

cache_script=$(node -e '
  const path = require("path")
  const menu = require(path.join(process.env.ROOT, "src/arch/shell/plugins/menu/MenuModel.js"))
  process.stdout.write(menu.guardScript({
    bash: { id: "bash", when: "arch-pkg-present bash" },
    vim: { id: "vim", when: "arch-pkg-present vim" },
    zen: { id: "zen", when: "arch-pkg-present zen-browser-bin" }
  }))
')

cache_case() {
  local dir="$cache_root/$1"
  mkdir -p "$dir/runtime" "$dir/db/local/bash-5.3-1" "$dir/db/local/gvim-9.2-1"
  echo "$dir"
}

# Runs the batch for a case, printing its answers on one line and leaving the
# pacman queries it made in $dir/pacman.log.
batch() {
  local dir=$1
  shift
  : >"$dir/pacman.log"
  env PATH="$cache_bin:$PATH" PACMAN_LOG="$dir/pacman.log" FIXTURE_DB="$dir/db" ARCH_PACMAN_DB_PATH="$dir/db" \
    XDG_RUNTIME_DIR="$dir/runtime" "$@" bash -e -c "$cache_script" | sort | tr '\n' ' '
}

queried() {
  [[ -s $1/pacman.log ]]
}

dir=$(cache_case reuse)
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "a first batch answers from pacman" "$(batch "$dir")"
queried "$dir" || fail "a first batch asks pacman"
[[ -f $dir/runtime/arch-menu-packages ]] || fail "a first batch stores the package set"
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "a cached batch answers as pacman did, provides included"
! queried "$dir" || fail "a batch over an unchanged database does not ask pacman" "$(<"$dir/pacman.log")"
pass "a batch over an unchanged package database answers from the stored set without asking pacman"

# Upgrades rename an entry, installs add one and removals drop one; each has
# to be seen by the very next batch.
mkdir "$dir/db/local/zen-browser-bin-1.0-1"
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:1 " ]] || fail "an install shows on the next batch" "$(batch "$dir")"
queried "$dir" || fail "an install makes the next batch ask pacman"
rmdir "$dir/db/local/gvim-9.2-1"
[[ $(batch "$dir") == "bash:w:1 vim:w:0 zen:w:1 " ]] || fail "a removal shows on the next batch, provides included" "$(batch "$dir")"
mv "$dir/db/local/bash-5.3-1" "$dir/db/local/bash-5.3-2"
batch "$dir" >/dev/null
queried "$dir" || fail "an upgrade makes the next batch ask pacman"
pass "installs, removals and upgrades reach the very next batch"

# Without the test seam the database is wherever pacman.conf puts it, so a
# DBPath away from /var/lib/pacman still moves the stamp the batch reads.
dir=$(cache_case dbpath)
batch "$dir" ARCH_PACMAN_DB_PATH= >/dev/null
[[ -f $dir/runtime/arch-menu-packages ]] || fail "the database pacman-conf names is cached"
mkdir "$dir/db/local/zen-browser-bin-1.0-1"
[[ $(batch "$dir" ARCH_PACMAN_DB_PATH=) == "bash:w:1 vim:w:1 zen:w:1 " ]] ||
  fail "an install in the database pacman-conf names reaches the next batch" "$(batch "$dir" ARCH_PACMAN_DB_PATH=)"
queried "$dir" || fail "an install in the database pacman-conf names makes the next batch ask pacman"
pass "the stamp follows the database pacman.conf's DBPath names"

# A database pacman is still writing must not be remembered: the entry can
# exist before its desc does, and nothing would move the stamp afterwards.
dir=$(cache_case locked)
touch "$dir/db/db.lck"
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "a batch during a transaction still answers" "$(batch "$dir")"
[[ ! -e $dir/runtime/arch-menu-packages ]] || fail "a batch during a transaction stores nothing"
rm "$dir/db/db.lck"
batch "$dir" >/dev/null
queried "$dir" || fail "the batch after a transaction asks pacman"
[[ -f $dir/runtime/arch-menu-packages ]] || fail "the batch after a transaction stores the set"
pass "a set read while pacman holds its lock is used once and never stored"

# A transaction that starts or finishes while the set is read leaves a set
# that may be missing its packages; the checks after the queries catch both.
for during in install lock; do
  dir=$(cache_case "during-$during")
  batch "$dir" PACMAN_DURING_QI="$during" >/dev/null
  queried "$dir" || fail "a batch asks pacman before a transaction lands mid-read ($during)"
  [[ ! -e $dir/runtime/arch-menu-packages ]] || fail "a set read across a transaction is never stored ($during)"
  rm -f "$dir/db/db.lck"
  [[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:$([[ $during == "install" ]] && echo 1 || echo 0) " ]] ||
    fail "the batch after a mid-read transaction answers from a fresh set ($during)" "$(batch "$dir")"
  queried "$dir" || fail "the batch after a mid-read transaction asks pacman again ($during)"
done
pass "a set read across a transaction that lands mid-read is used once and never stored"

# A failed query answers for its own batch, as before, but an empty or
# provide-less set stored now would hide rows until the next transaction.
dir=$(cache_case failed)
[[ $(batch "$dir" PACMAN_QI_FAILS=1) == "bash:w:1 vim:w:0 zen:w:0 " ]] || fail "a failed query answers for its own batch" "$(batch "$dir" PACMAN_QI_FAILS=1)"
[[ ! -e $dir/runtime/arch-menu-packages ]] || fail "a failed query is never stored"
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "the batch after a failed query asks again" "$(batch "$dir")"
pass "a set from a failed pacman query is never stored"

# A set stored under another stamp is never believed.
dir=$(cache_case stale)
printf '%s\n' "0:0:0:0" bash gvim vim zen-browser-bin >"$dir/runtime/arch-menu-packages"
[[ $(batch "$dir") == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "a set stored under another stamp is ignored" "$(batch "$dir")"
queried "$dir" || fail "a set stored under another stamp makes the batch ask pacman"
pass "a set stored under another database stamp is ignored and replaced"

dir=$(cache_case no-runtime)
[[ $(batch "$dir" XDG_RUNTIME_DIR=) == "bash:w:1 vim:w:1 zen:w:0 " ]] || fail "a batch without a runtime dir still answers"
[[ -z $(ls -A "$dir/runtime") ]] || fail "a batch without a runtime dir stores nothing"
pass "a batch without a runtime dir asks pacman and stores nothing"
