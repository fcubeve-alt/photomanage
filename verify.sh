#!/usr/bin/env bash
# Everything this machine can check, in one command. Run it before every push.
#
# This exists because of a specific mistake: `invoice` was added to
# `30_ENGINE/pvm/rules.py` and the generated Swift was not regenerated, so the app's
# rules and the engine's disagreed for two commits. CI caught it — on a macOS runner
# billed at ten times the Linux rate, one push later, after a queue. Every check below
# is free and takes seconds; the value is having one command to remember instead of
# five, because the one that gets skipped is the one that catches the drift.
#
# What it cannot check: anything needing a Swift compiler (this machine has none —
# `download.swift.org` is blocked by the egress policy), an Apple platform, or a device.
# `swift-core.yml` covers Swift on Linux; `app-build.yml` covers the app; neither is a
# device result (PF-01).

set -u
cd "$(dirname "$0")"
failures=0

# Output goes to a file and the tail is printed from it, rather than being piped.
#
# The first version piped each command into `tail` to keep the output short, and so
# reported the exit status of `tail` — which is always 0. It printed "ok" under a run
# with a failing test. `set -o pipefail` does not fix it either, because the commands
# run inside `bash -c` and that inner shell does not inherit the option.
#
# A check that cannot fail is worse than no check: it is a check you trust. `--selftest`
# below proves this one still can.
step() {
  local title="$1"; shift
  printf '\n\033[1m▸ %s\033[0m\n' "$title"
  local log
  log="$(mktemp)"
  if "$@" > "$log" 2>&1; then
    tail -3 "$log" | sed 's/^/  /'
    printf '  ok\n'
  else
    tail -25 "$log" | sed 's/^/  /'
    printf '  \033[31mFAILED\033[0m\n'
    failures=$((failures + 1))
  fi
  rm -f "$log"
}

run_all() {
  step "Engine — behaviour and safety tests" \
    bash -c 'cd 30_ENGINE && python3 -m unittest discover -s tests -q'

  step "Binding constraints still match the source documents" \
    bash -c 'cd 30_ENGINE && python3 check_constraints.py'

  step "Gate 2 — entity resolver self-test" \
    bash -c 'cd 30_ENGINE && python3 eval/evaluate_entities.py --selftest'

  step "Gate 2 — Document False Merge is still zero" \
    bash -c 'cd 30_ENGINE && python3 eval/evaluate_entities.py | grep "Document False Merge: 0 of"'

  step "Classifier evaluation self-test" \
    bash -c 'cd 30_ENGINE && python3 eval/evaluate.py --selftest'

  # The one that would have caught the invoice drift.
  step "The app's shared Swift still matches the engine" \
    python3 40_APP/generate_shared.py --check
}

# `./verify.sh --selftest` breaks something on purpose and checks that this script
# notices. Without it, the guard is only as trustworthy as the last time anyone looked.
if [ "${1:-}" = "--selftest" ]; then
  probe="30_ENGINE/tests/test_engine.py"
  cp "$probe" "$probe.bak"
  printf '\n\nclass VerifySelfTest(unittest.TestCase):\n' >> "$probe"
  printf '    def test_deliberately_failing(self):\n        self.fail("verify.sh selftest")\n' >> "$probe"
  run_all > /dev/null 2>&1
  mv "$probe.bak" "$probe"
  if [ "$failures" -gt 0 ]; then
    printf 'selftest: verify.sh reports failures when a test fails — ok\n'
    exit 0
  fi
  printf 'SELFTEST FAIL: a failing test did not make verify.sh fail\n'
  exit 1
fi

run_all
printf '\n'
if [ "$failures" -eq 0 ]; then
  printf '\033[32mall local checks passed\033[0m — Swift itself is only verified in CI\n'
else
  printf '\033[31m%d check(s) failed\033[0m — do not push\n' "$failures"
fi
exit "$failures"
