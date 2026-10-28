#!/bin/bash
#
# arch-sudo-docker answers whether this session can reach the Docker socket.

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

command="$ROOT/src/arch/commands/arch-sudo-docker"

mkdir -p "$TMPDIR/bin"

# A writable stand-in means the socket is reachable; an unwritable one means it
# is not. Test the file mode rather than a live daemon.
reachable_socket="$TMPDIR/reachable.sock"
blocked_socket="$TMPDIR/blocked.sock"
touch "$reachable_socket" "$blocked_socket"
chmod 600 "$reachable_socket"
chmod 400 "$blocked_socket"

run() { # SOCKET
  env PATH="$TMPDIR/bin:$PATH" ARCH_DOCKER_SOCKET="$1" bash "$command" ${2:+"$2"}
}

# Default mode follows the socket, not the group list.
run "$blocked_socket" || fail "an unreachable socket means Docker needs sudo"
run "$reachable_socket" && fail "a reachable socket means Docker does not need sudo"
pass "default mode answers from the socket this session can reach"

# A socket that isn't there at all still needs elevation (starting it is root work).
run "$TMPDIR/absent.sock" || fail "a missing socket means Docker needs sudo"
pass "a missing socket counts as needing sudo"

# An unknown argument is a usage error, not a silent answer either way.
run "$reachable_socket" --bogus 2>/dev/null && fail "an unknown flag exits non-zero"
status=0
run "$reachable_socket" --bogus >/dev/null 2>&1 || status=$?
(( status == 2 )) || fail "an unknown flag exits 2, not the boolean 1"
pass "an unknown flag is a usage error"
