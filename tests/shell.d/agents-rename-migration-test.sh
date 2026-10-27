#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

require_command jq

migration="$ROOT/migrations/1786099804.sh"
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT

mkdir -p "$test_dir/bin"

cat >"$test_dir/bin/arch-agent-usage-update" <<'STUB'
#!/bin/bash

echo run >>"$USAGE_UPDATES"
STUB

chmod +x "$test_dir/bin/"*

export USAGE_UPDATES="$test_dir/usage-updates"

home="$test_dir/home"
config="$home/.config/arch/shell.json"

run_migration() {
  : >"$USAGE_UPDATES"
  HOME="$home" PATH="$test_dir/bin:$PATH" bash -euo pipefail "$migration" >/dev/null
}

mkdir -p "$home/.config/arch" "$home/.cache/arch/model-usage"
cat >"$config" <<'JSON'
{
  "bar": {
    "layout": {
      "center": ["arch.model-usage"],
      "right": [
        { "id": "arch.tray" },
        { "id": "arch.model-usage", "syncMode": "On", "syncDir": "~/Sync/agent-usage" }
      ]
    }
  },
  "disabledPlugins": ["arch.model-usage", "arch.weather"]
}
JSON

run_migration

[[ $(jq -c '.bar.layout.right[1]' "$config") == '{"id":"arch.agents","syncMode":"On","syncDir":"~/Sync/agent-usage"}' ]] ||
  fail "migration renames the widget and keeps its settings" "$(cat "$config")"
pass "migration renames the widget and keeps its settings"

[[ $(jq -c '.bar.layout.center' "$config") == '["arch.agents"]' ]] ||
  fail "migration renames string-form entries" "$(cat "$config")"
pass "migration renames string-form entries"

[[ $(jq -c '.disabledPlugins' "$config") == '["arch.agents","arch.weather"]' ]] ||
  fail "migration keeps a disabled widget disabled" "$(cat "$config")"
pass "migration keeps a disabled widget disabled"

[[ ! -e $home/.cache/arch/model-usage ]] ||
  fail "migration drops the old scanner cache"
pass "migration drops the old scanner cache"

(($(wc -l <"$USAGE_UPDATES") == 1)) || fail "migration primes the usage data files"
pass "migration primes the usage data files"

before=$(sha256sum "$config")
run_migration
[[ $before == $(sha256sum "$config") ]] || fail "legacy migration is idempotent" "$(cat "$config")"
pass "legacy migration is idempotent"

retire_migration="$ROOT/migrations/1793067182.sh"
bash -euo pipefail "$retire_migration" >/dev/null
[[ $(jq -c '.bar.layout.right' "$config") == '[{"id":"arch.tray"}]' ]] ||
  fail "retirement removes the agent widget but preserves other layout entries" "$(cat "$config")"
[[ $(jq -c '.bar.layout.center' "$config") == '[]' ]] ||
  fail "retirement removes string-form agent widget entries" "$(cat "$config")"
[[ $(jq -c '.disabledPlugins' "$config") == '["arch.weather"]' ]] ||
  fail "retirement removes the obsolete disabled plugin id" "$(cat "$config")"
pass "retirement removes the obsolete agent widget from existing shell configs"

before=$(sha256sum "$config")
bash -euo pipefail "$retire_migration" >/dev/null
[[ $before == $(sha256sum "$config") ]] || fail "widget retirement is idempotent" "$(cat "$config")"
pass "widget retirement is idempotent"

# A config the migration cannot parse is left alone rather than truncated.
printf '{ not json' >"$config"
run_migration

[[ $(cat "$config") == '{ not json' ]] || fail "migration leaves an unparsable config untouched" "$(cat "$config")"
pass "migration leaves an unparsable config untouched"
