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
#
# **So the order to run CI in is swift-core FIRST, and app-build only once it is green.**
# On 2026-09-07 an app-build run was dispatched at the same moment as the push and died
# in 38 seconds on two Swift compile errors — a wrong type name and an Optional binding
# on a non-Optional — on a macOS runner billed at ten times the Linux rate. The Linux
# job compiles the same sources in about a minute and would have said the same thing.
# Nothing here can catch that class of error; sequencing the two jobs can.

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

  # And the one that would have caught the media_type drift. The generator covers the
  # taxonomy and the rules because those are generated; the schema is hand-written in
  # both files, so nothing was comparing them.
  step "Both catalogues have the same shape" \
    python3 40_APP/check_schema.py

  # P0-2. The read-only guarantee, enforced at the only level that can enforce
  # "this code does not exist yet": a grep over the shipping sources.
  #
  # Until a third-party audit pointed it out on 2026-09-11, "this app never deletes a
  # photo" was true because nobody had written the code — a safety property holding by
  # absence, which stops holding the day someone finishes the feature, with no test
  # failing. `LibrarySafety` is the runtime gate; this is the one that notices a write
  # arriving that never went through it.
  step "No PhotoKit write reaches the library except through LibrarySafety" \
    python3 40_APP/check_no_photo_writes.py

  # The state documents claim things about the world — visibility, which branch the
  # work is on, whether the product exists. `recovery_check.py` checks they are
  # coherent; this checks they are TRUE, which is a different question and is the one
  # a third-party audit answered for us on 2026-09-11.
  step "The state documents still describe the actual repository" \
    python3 check_repo_reality.py
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
