arch_log_to_stdout() {
  [[ ${ARCH_LOG_TO_STDOUT:-} == "1" || -z ${ARCH_INSTALL_LOG_FILE:-} ]]
}

arch_log_line() {
  if arch_log_to_stdout; then
    echo "$1"
  else
    echo "$1" >>"$ARCH_INSTALL_LOG_FILE"
  fi
}

start_install_log() {
  if ! arch_log_to_stdout; then
    mkdir -p "$(dirname "$ARCH_INSTALL_LOG_FILE")"
    if [[ -L $ARCH_INSTALL_LOG_FILE ]]; then
      return 1
    fi
    if [[ -e $ARCH_INSTALL_LOG_FILE ]]; then
      [[ -f $ARCH_INSTALL_LOG_FILE ]] || return 1
      chmod 600 -- "$ARCH_INSTALL_LOG_FILE" || return 1
    fi
    if ! (umask 077; touch -- "$ARCH_INSTALL_LOG_FILE"); then
      return 1
    fi
    chmod 600 -- "$ARCH_INSTALL_LOG_FILE" || return 1
  fi

  export ARCH_START_TIME="${ARCH_START_TIME:-$(date '+%Y-%m-%d %H:%M:%S')}"
  export ARCH_START_EPOCH="${ARCH_START_EPOCH:-$(date +%s)}"

  arch_log_line "=== os Setup Started: $ARCH_START_TIME ==="
}

stop_install_log() {
  local end_time end_epoch duration mins secs
  end_time=$(date '+%Y-%m-%d %H:%M:%S')
  end_epoch=$(date +%s)

  arch_log_line "=== os Setup Completed: $end_time ==="

  if [[ -n ${ARCH_START_EPOCH:-} ]]; then
    duration=$((end_epoch - ARCH_START_EPOCH))
    mins=$((duration / 60))
    secs=$((duration % 60))
    arch_log_line "os setup: ${mins}m ${secs}s"
  fi
}

run_logged() {
  local script="$1"
  local exit_code errexit_was_set=0

  arch_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $script"

  case $- in
    *e*)
      errexit_was_set=1
      set +e
      ;;
  esac

  local -a runner
  if [[ $script == *.py ]]; then
    runner=(python3 -I "$script")
  else
    runner=(bash -eE)
    if [[ ${ARCH_INSTALL_DEBUG:-} == "1" ]]; then
      runner=(bash -x -eE)
    fi
  fi

  if arch_log_to_stdout; then
    if [[ $script == *.py ]]; then
      "${runner[@]}" </dev/null 2>&1
    else
      PS4='+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: ' \
        "${runner[@]}" -c 'source "$1"' bash "$script" </dev/null 2>&1
    fi
  else
    if [[ $script == *.py ]]; then
      "${runner[@]}" </dev/null >>"$ARCH_INSTALL_LOG_FILE" 2>&1
    else
      PS4='+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: ' \
        "${runner[@]}" -c 'source "$1"' bash "$script" </dev/null >>"$ARCH_INSTALL_LOG_FILE" 2>&1
    fi
  fi

  exit_code=$?
  (( errexit_was_set )) && set -e

  if (( exit_code == 0 )); then
    arch_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Completed: $script"
  else
    arch_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Failed: $script (exit code: $exit_code)"
  fi

  return $exit_code
}
