#!/usr/bin/env bash
# Everything this machine can check, in one command. Run it before every push.
#
# This exists because of a specific mistake: `invoice` was added to
# `30_ENGINE/pvm/rules.py` and the generated Swift was not regenerated, so the app's
# rules and the engine's disagreed for two commits. CI caught it — on a macOS runner
# billed at ten times the Linux rate, one push later, after a queue. Every check below
# is free and takes seconds; the value is that there is one command to remember instead
# of five, because the one that gets skipped is the one that catches the drift.
#
# What it cannot check: anything needing a Swift compiler (this machine has none —
# `download.swift.org` is blocked by the egress policy), an Apple platform, or a device.
# `swift-core.yml` covers Swift on Linux; `app-build.yml` covers the app; neither is a
# device result (PF-01).

set -uo pipefail
cd "$(dirname "$0")"
failures=0

step() {
  printf '\n\033[1m▸ %s\033[0m\n' "$1"; shift
  if "$@"; then
    printf '  ok\n'
  else
    printf '  \033[31mFAILED\033[0m\n'
    failures=$((failures + 1))
  fi
}

step "Engine — behaviour and safety tests" \
  bash -c 'cd 30_ENGINE && python3 -m unittest discover -s tests -q 2>&1 | tail -3'

step "Binding constraints still match the source documents" \
  bash -c 'cd 30_ENGINE && python3 check_constraints.py | tail -2'

step "Gate 2 — entity resolver self-test" \
  bash -c 'cd 30_ENGINE && python3 eval/evaluate_entities.py --selftest'

step "Gate 2 — Document False Merge is still zero" \
  bash -c 'cd 30_ENGINE && python3 eval/evaluate_entities.py | grep "Document False Merge: 0 of"'

step "Classifier evaluation self-test" \
  bash -c 'cd 30_ENGINE && python3 eval/evaluate.py --selftest | tail -2'

# The one that would have caught the invoice drift.
step "The app's shared Swift still matches the engine" \
  python3 40_APP/generate_shared.py --check

printf '\n'
if [ "$failures" -eq 0 ]; then
  printf '\033[32mall local checks passed\033[0m — Swift itself is only verified in CI\n'
else
  printf '\033[31m%d check(s) failed\033[0m — do not push\n' "$failures"
fi
exit "$failures"
