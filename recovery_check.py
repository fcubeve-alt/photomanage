#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COLD-START RECOVERY TEST — Playbook §5 Bootstrap Checklist, last unchecked item.

    "做一次 Cold-Start Recovery Test：假设换了新模型/新 Session，
     验证能否不靠 Owner 解释继续。"

Asserting that recovery works is worthless. This checks it mechanically, and it is
meant to be re-run whenever the state files change — recovery rots silently as
documents drift apart.

What it verifies:
  1. Every canonical state file exists.
  2. The handoff coordinates match REALITY (git remote, branch, HEAD), not what
     someone wrote down three days ago.
  3. Every internal link in the state files resolves. A dead link in PROJECT_STATE
     is a recovery failure, not a typo.
  4. The seven questions a cold session must answer are actually answerable from the
     documented reading order.
  5. No stale claims — the classic being a document still saying "no remote" after
     one exists.
  6. Environment traps a fresh session would otherwise hit are recorded.
  7. SEMANTIC staleness — documents that resolve perfectly while saying something
     untrue. Added after this checker reported 0 FAIL while MASTER_PLAN contradicted
     itself about the current milestone and MISSION_SPEC defined HG-5 twice.

    python recovery_check.py            # report
    python recovery_check.py --strict   # non-zero exit if anything fails
"""

import os, re, subprocess, sys
# Output is UTF-8 regardless of console locale (PF-10 — cp936 cannot encode the
# report glyphs and the tool would die after doing all the work).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


ROOT = os.path.dirname(os.path.abspath(__file__))

CANONICAL = [
    "README.md", "PROJECT_STATE.md", "SESSION_HANDOFF.md", "MISSION_SPEC.md",
    "MASTER_PLAN.md", "OPERATING_RULES.md", "DECISIONS.md", "FAILURE_PATTERNS.md",
    "DOCUMENTATION_MAP.md", "VALIDATION_MATRIX.md", "CONSTITUTION_UNDERSTANDING.md",
    "ARCHITECTURE_METHODOLOGY.md",
]

# The questions a session with NO conversation history must be able to answer.
QUESTIONS = [
    ("What is this project and what stage is it in?",
     "PROJECT_STATE.md", [r"Personal Visual Memory", r"Tier 0"]),
    ("Which document is authoritative for product decisions?",
     "PROJECT_STATE.md", [r"Constitution.*v1\.3", r"CONSTITUTION_UNDERSTANDING"]),
    ("What has been done and what has not?",
     "PROJECT_STATE.md", [r"[Dd]one", r"NOT RUN|zero measurements|not tested|NOT TESTED"]),
    ("What is the next action?",
     "PROJECT_STATE.md", [r"[Nn]ext action"]),
    ("What must I NOT redo?",
     "SESSION_HANDOFF.md", [r"Do NOT repeat|do not repeat"]),
    ("What is blocked and on whom?",
     "PROJECT_STATE.md", [r"HUMAN_GATE|HG-1|HG-4"]),
    ("What environment traps will bite me?",
     "SESSION_HANDOFF.md", [r"git.*2\.9|TOOLING|tools[\\/]git"]),
]

results = []


def ok(cat, msg):
    results.append(("OK", cat, msg))


def fail(cat, msg):
    results.append(("FAIL", cat, msg))


def warn(cat, msg):
    results.append(("WARN", cat, msg))


def git(*args):
    for exe in (r"C:\Users\admin\tools\git\cmd\git.exe", "git"):
        try:
            out = subprocess.run([exe] + list(args), cwd=ROOT, capture_output=True,
                                 text=True, timeout=30)
            if out.returncode == 0:
                return out.stdout.strip()
        except Exception:
            continue
    return None


def build_index():
    """filename -> [relative paths]. Guessing candidate directories produced false
    positives, and a checker that cries wolf gets ignored."""
    idx = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "__pycache__", "site", "prototype",
                                    "library", "_extracted_text", "90_ARCHIVE")]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
            idx.setdefault(fn, []).append(rel)
    return idx


FILE_INDEX = build_index()


def resolve(target):
    """True if the reference points at something that exists, by path or by name."""
    t = target.replace("\\", "/").lstrip("./")
    if os.path.exists(os.path.join(ROOT, t)):
        return True
    return os.path.basename(t) in FILE_INDEX


def read(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="ignore").read()


# --- 1. canonical files -----------------------------------------------------
for f in CANONICAL:
    if os.path.exists(os.path.join(ROOT, f)):
        ok("files", f)
    else:
        fail("files", f"MISSING canonical state file: {f}")

# --- 2. coordinates match reality ------------------------------------------
branch = git("rev-parse", "--abbrev-ref", "HEAD")
remote = git("remote", "get-url", "origin")
head = git("rev-parse", "--short", "HEAD")
dirty = git("status", "--porcelain")

handoff = read("SESSION_HANDOFF.md") or ""
state = read("PROJECT_STATE.md") or ""

if remote:
    ok("git", f"remote: {remote}")
    if re.search(r"remote.*\bnone\b|local[- ]only", handoff + state, re.I):
        fail("stale", "a state file still claims there is NO remote, but one exists — "
                      "a cold session would waste time re-solving a solved problem")
    else:
        ok("stale", "no document still claims 'local only'")
    slug = remote.rstrip("/").split("/")[-1].replace(".git", "")
    if slug in handoff or slug in state:
        ok("git", f"repo name '{slug}' appears in the state files")
    else:
        warn("git", f"repo name '{slug}' not mentioned in PROJECT_STATE/SESSION_HANDOFF")
else:
    fail("git", "no git remote — E-06 cross-machine recovery is not possible")

if branch:
    ok("git", f"branch: {branch}")
    if branch in handoff or branch in state:
        ok("git", "branch recorded in state files")
    else:
        warn("git", f"branch '{branch}' not recorded in state files")

if dirty is not None:
    if dirty.strip():
        warn("git", f"working tree has {len(dirty.splitlines())} uncommitted change(s) — "
                    "a cold session would inherit them without knowing why")
    else:
        ok("git", "working tree clean — nothing uncommitted to explain")

# --- 3. internal links resolve ---------------------------------------------
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
broken = []
checked = 0
for f in CANONICAL:
    body = read(f)
    if not body:
        continue
    for m in LINK.finditer(body):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        target = target.split(":")[0] if re.search(r"\.md:\d+$", target) else target
        checked += 1
        if not resolve(target):
            broken.append(f"{f} → {target}")
if broken:
    for b in broken:
        fail("links", f"dead link: {b}")
elif checked == 0:
    # An empty check must not report green. The state files reference files with
    # backticks rather than markdown links, so the `refs` check is the real one.
    warn("links", "no markdown links in the state files — this check is vacuous here; "
                  "the backtick `refs` check is the one that matters")
else:
    ok("links", f"all {checked} internal links resolve")

# --- 4. backtick file references in the state files -------------------------
REF = re.compile(r"`([0-9A-Za-z_./\\-]+\.(?:md|py|swift|yml|csv|json))`")
missing_refs = set()
ref_count = 0
for f in ("PROJECT_STATE.md", "SESSION_HANDOFF.md"):
    body = read(f) or ""
    for m in REF.finditer(body):
        t = m.group(1).replace("\\", "/")
        if t.startswith(("http", "~")) or "*" in t:
            continue
        ref_count += 1
        if not resolve(t):
            missing_refs.add(f"{f} → {t}")
if missing_refs:
    for r in sorted(missing_refs):
        warn("refs", f"referenced file not found: {r}")
else:
    ok("refs", f"all {ref_count} file references in the handoff chain resolve")

# --- 5. the seven questions -------------------------------------------------
for q, src, pats in QUESTIONS:
    body = read(src) or ""
    hit = all(re.search(p, body, re.I) for p in pats)
    (ok if hit else fail)("answerable", f"{'' if hit else 'UNANSWERABLE: '}{q}  [{src}]")

# --- 6. evidence honesty ----------------------------------------------------
gate = read(os.path.join("20_TIER0", "TIER0_GO_NO_GO.md")) or ""
if gate:
    if re.search(r"NOT REACHED|template, not a result", gate, re.I):
        ok("honesty", "gate document states plainly that it is not a result")
    else:
        fail("honesty", "TIER0_GO_NO_GO.md does not clearly state it is unfilled")
ev = os.path.join(ROOT, "20_TIER0", "evidence")
if os.path.isdir(ev):
    files = [f for f in os.listdir(ev) if f.endswith(".md")]
    ok("honesty", f"evidence dir holds {len(files)} completed artifact(s): {files}")

# --- 7. reading order is stated --------------------------------------------
if re.search(r"Must read|读|reading order", handoff, re.I):
    ok("order", "SESSION_HANDOFF states an explicit reading order")
else:
    fail("order", "no reading order in SESSION_HANDOFF — a cold session has no entry point")


# --- 8. semantic staleness ---------------------------------------------------
# The link/ref checks verify that references RESOLVE. They cannot see a document
# that resolves perfectly while saying something untrue. Both defects below existed
# while this checker reported 0 FAIL, which is exactly why they are now checked.

plan = read("MASTER_PLAN.md") or ""
mission = read("MISSION_SPEC.md") or ""

# 8a. MASTER_PLAN's headline position must agree with PROJECT_STATE's stage.
# Tolerate both "**Current position: X**" and "Current position: **X**".
m_pos = re.search(r"Current position:\s*\**([^*\n]+)", plan)
m_stage = re.search(r"^- Stage:\s*(.+)$", state, re.M)
if m_pos and m_stage:
    pos, stage = m_pos.group(1), m_stage.group(1)
    pos_m = set(re.findall(r"\bM\d\b", pos))
    # Compare the milestone each file claims is CURRENT. Substring tests like
    # ("M1" in pos) cannot distinguish "M1 in progress" from "M1 complete" and
    # silently pass on a real contradiction — verified by negative control.
    cur_plan = re.search(r"\b(M\d)\b[^·|]{0,60}?IN PROGRESS", pos, re.I)
    cur_state = re.search(r"\b(M\d)\b", stage)
    if cur_plan and cur_state:
        if cur_plan.group(1) == cur_state.group(1):
            ok("staleness", f"MASTER_PLAN and PROJECT_STATE agree the current milestone "
                            f"is {cur_state.group(1)} ({stage.strip()})")
        else:
            fail("staleness", f"MASTER_PLAN says {cur_plan.group(1)} is in progress but "
                              f"PROJECT_STATE says {cur_state.group(1)} — a cold session "
                              f"would read the wrong milestone off the top line")
    else:
        warn("staleness", "could not identify the current milestone in both files "
                          f"(plan={'yes' if cur_plan else 'no'}, "
                          f"state={'yes' if cur_state else 'no'})")
    # Internal contradiction: claiming a milestone is complete AND in progress.
    # The section must be ISOLATED first. A DOTALL search starting at one heading
    # runs on into the next milestone and finds ITS status — which produced a false
    # FAIL here, the same cry-wolf failure this checker already had once.
    for mid in pos_m:
        sec = re.search(rf"^##\s*{mid}\b(.*?)(?=^##\s|\Z)", plan, re.S | re.M)
        if not sec:
            continue
        if re.search(r"IN PROGRESS", sec.group(1), re.I) and \
           re.search(rf"{mid}\s*complete", pos, re.I):
            fail("staleness", f"MASTER_PLAN calls {mid} complete in the header while the "
                              f"{mid} section is marked IN PROGRESS")
else:
    warn("staleness", "could not locate MASTER_PLAN position or PROJECT_STATE stage")

# 8b. Human Gate ids must be unique. A duplicated id makes "HG-5 is blocking"
# ambiguous, which is worse than having no id.
gate_ids = re.findall(r"^\|\s*\*{0,2}(HG-\d[a-z]?)\*{0,2}\s*\|", mission, re.M)
dupes = {g for g in gate_ids if gate_ids.count(g) > 1}
if dupes:
    fail("staleness", f"duplicate Human Gate id(s) in MISSION_SPEC: {sorted(dupes)} — "
                      "'HG-x is blocking' becomes ambiguous")
elif gate_ids:
    ok("staleness", f"{len(gate_ids)} Human Gate ids, all unique")

# 8c. Gate ids referenced in PROJECT_STATE should be defined in MISSION_SPEC.
referenced = set(re.findall(r"\bHG-\d[a-z]?", state))
defined = set(gate_ids)
undefined = referenced - defined
if undefined:
    fail("staleness", f"PROJECT_STATE references gate(s) NOT defined in MISSION_SPEC: "
                      f"{sorted(undefined)} — the gate table is the single source of truth")
elif referenced:
    ok("staleness", f"all {len(referenced)} gate ids used in PROJECT_STATE are defined")

# ---------------------------------------------------------------------------
print("COLD-START RECOVERY TEST")
print("=" * 72)
print("Simulates: new session, new model, new machine. Repo + state files only,")
print("no conversation history, no Owner explanation available.")
print("=" * 72)

order = {"FAIL": 0, "WARN": 1, "OK": 2}
for status, cat, msg in sorted(results, key=lambda r: (order[r[0]], r[1])):
    mark = {"OK": " ok ", "WARN": "WARN", "FAIL": "FAIL"}[status]
    print(f"[{mark}] {cat:<11} {msg}")

nf = sum(1 for r in results if r[0] == "FAIL")
nw = sum(1 for r in results if r[0] == "WARN")
print("=" * 72)
print(f"{len(results)} checks · {nf} FAIL · {nw} WARN")
if nf:
    print("\nRECOVERY WOULD BE DEGRADED. A fresh session would have to ask the Owner,")
    print("or would rediscover something already solved. Fix before relying on it.")
else:
    print("\nRECOVERY VIABLE — a fresh session can reach the next action unaided.")
if "--strict" in sys.argv and nf:
    sys.exit(1)
