# OPERATING RULES
Inherited from Cross-Project Engineering Playbook v1.1 (L3), filtered for this project per Playbook §6.
These are the rules any session/model must load before working. Project product truth stays in the Constitution.

## Installed layers
- **Layer A — Engineering Core (E-01…E-15): RESIDENT, all of it.**
- **Layer B — Autonomous Supervisor (S-01…S-10): RESIDENT.** This project runs long autonomous stretches, so it is enabled. S-10 applies at material gates.
- **Layer C — Business Opportunity Governance: ON DEMAND ONLY.** Load it for Tier 0-C (competitor/pricing/payment-signal work) and for the Tier gates. Do not keep it resident during engineering work.
- **§5A Context / Token Protocol (T-01…T-17): RESIDENT, mandatory.**
- **NOT installed:** any Money OS / Project M / KDP / Vocal / UEFN business content, platform conclusions or market assumptions. Those are the *source* of these lessons, not requirements of this project.

## Engineering Core — the ones that bite hardest here
| Rule | Applied form in this project |
|---|---|
| E-01 Mission ≠ plan | Constitution v1.3 goals are fixed. Tier ordering and technique are adjustable on evidence. |
| E-02 Owner WHAT / AI HOW | Never silently rewrite scope. Scope change = HG-6. |
| E-03 Canonical state on disk | `PROJECT_STATE.md` is the entry point every session. Chat is not the database. |
| E-04 Session disposable, state is not | Model/window/quota changes are normal events, not incidents. |
| E-05 Bootstrap integrity check | New session: read `PROJECT_STATE.md` → `SESSION_HANDOFF.md` → `git status --short` → `git log --oneline -5`. Only then work. |
| E-06 Local absence ≠ remote absence | Never rebuild something because this machine cannot see it. |
| E-07 Incremental checkpoint | Research/benchmarks/labelling save per small batch. Max loss = last batch. |
| E-08 Capability failure ≠ mission failure | Web search down → switch to search-free queue, do not idle. |
| E-09 / T-10 Reuse | Evidence store carries source + date + confidence + freshness. Do not re-research a fresh fact. |
| E-10 / T-11 / T-15 **Optimize Waste, Not Thinking** | Cut rereads, rescans, duplicate tests, useless tokens. Never cut necessary reasoning, real tests or a Kill Test. |
| E-12 Minimum necessary verification | Targeted check after each change; wider regression at milestones. Written code ≠ working feature. |
| E-13 FACT / INTERPRETATION / RECOMMENDATION | Mandatory format for all competitor, pricing, platform and Apple-capability claims. |
| E-14 Evidence scope | A conclusion covers only what was actually tested. A desktop measurement is never an iPhone result. |
| E-15 Learn once | Every real failure becomes an entry in `FAILURE_PATTERNS.md`. |

## Autonomous Supervisor — applied form
- **S-01** Finishing a task does not end the mission: persist → recompute the queue → start the next highest-value executable item.
- **S-02** Persistent queue lives in `PROJECT_STATE.md` under lanes ACTIVE / RESEARCH / EXPERIMENT / HUMAN_GATE / CAPABILITY / MAINTENANCE.
- **S-03** A blocked branch blocks only itself. T0-A being Mac-blocked must never stop T0-C1.
- **S-04** Entering WAITING requires proving nothing authorised and worthwhile is executable.
- **S-07** Every WAITING entry records blocker, wake_condition and first action after wake.
- **S-09** Agent/task status must be evidenced by artifacts, never merely claimed.

## Project-specific rules (added by this project)
- **P-01 One Tier at a time.** Later-Tier docs are readable for planning; implementing their tasks is forbidden until the prior gate file exists. Source: P0 Execution Index v1.0.
- **P-02 No fabricated device evidence.** Anything needing macOS/Xcode/real iPhone is tagged `REQUIRES_MAC` / `REQUIRES_DEVICE` and reported as untested. A Windows model may *predict* device behaviour; it may never be recorded as a device PASS.
- **P-03 Safety red lines are live from Tier 0.** No silent permanent deletion. IDs / contracts / family memories default to Protect. Every suggestion must carry a why-slot, even in a throwaway prototype.
- **P-04 On-device AI route is decided by benchmark, not by name.** Test Apple-native capability first. Do not add a 2GB+ model dependency without evidence that native capability fails a specific requirement.
- **P-05 Do not optimise for FP=0.** Report Automation Ratio, Human Review Burden, Weighted Error Cost, Catastrophic Error Rate, Significant Value Loss Rate together. Source: Constitution §7, §18, §20.
- **P-06 Read the extracted text, not the .docx.** `10_SOURCE_DOCS/_extracted_text/*.txt` is the grep surface. Re-parsing Word files each session is exactly the waste T-01/T-07 forbid.
- **P-07 Business-model work loads Layer C, then unloads it.** Competitor and pricing conclusions additionally require an Evidence Gate pack (Playbook §8) because they can kill or pivot a direction.
