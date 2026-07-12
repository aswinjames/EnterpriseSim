# BENCH-04 — Planning

| Field | Value |
|---|---|
| Suite | `BENCH-04` |
| Name | Planning |
| Primarily exercises | Decision Intelligence (`ARCH-06`) |
| Canon / Arch | `CANON-001` §9 (Stage 3), §4/§7 (standards), `ARCH-06`, `ARCH-04` |
| Owner | AI Engineering (`TEAM-070`) + Architecture Office (`TEAM-090`) |

---

## Purpose

Measure whether the Worker produces an explicit, testable, standards-compliant **plan**
(`PLAN-###`) from context: the ordered steps, target artifacts, tests, risk tier and rollback
strategy that a plan is (`ARCH-06`). A plan is a *commitment* the Worker can be evaluated
against, so plan quality gates everything downstream.

## What it measures

- **Completeness** — steps cover the task; required elements present (tests, rollback, risk tier).
- **Standards compliance** — correct risk tier and approval count (`CANON-001` §7), rollback
  strategy declared, negative-side-effect assertions where experience demands them.
- **Sequencing correctness** — respects the dependency graph (`APP-012` auth precedes `APP-010`
  inventory commit) and does not propose forbidden reverse dependencies.
- **Success-criteria quality** — criteria are concrete and checkable, not vague.

## Task design

Given a task trigger and an assembled context (fixed, so this suite isolates planning from
retrieval), the Worker emits a `PLAN-###`. The reference is the canonical plan (`PLAN-0072`) and
its rubric. Cases include a **Tier-0/PCI** variant (must require 2 approvals + threat-model
check), a **rollback-required** variant, and a **negative-test** variant (must include the
`GuestNoLoyaltyTest`-style assertion because `EXP-090` is in context).

## Inputs

- `inputs.trigger` and `inputs.context` — the fixed `CTX-###` working set (incl. `EXP-090`).
- `inputs.standards` — the applicable `CANON-001` §4/§7 excerpts (risk tiers, approvals).

## Ground truth

`type: rubric_only` with objective sub-checks — plan adequacy is partly qualitative, but the
non-negotiable elements are machine-checkable (`source: PLAN-0072`):

- required elements present: `steps`, `rollback`, `risk_tier`, ≥1 negative/success criterion.
- `must_include` structural facts: risk_tier = 0 for `APP-003`; rollback via feature flag; a
  negative assertion guarding `APP-015`.
- forbidden: any step implying a reverse dependency.

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `required_elements_present` | objective | 0.25 | Steps, rollback, risk tier, success criteria all present. |
| `standards_compliance` | objective | 0.25 | Correct risk tier / approvals; rollback declared (`CANON-001` §7). |
| `dependency_sequencing` | objective | 0.20 | Correct order; no forbidden reverse dependency (hard gate). |
| `negative_assertion_present` | objective | 0.10 | Includes the side-effect guard experience demands. |
| `plan_adequacy` | rubric | 0.20 | Would a senior MCG engineer accept this plan? (independent judge). |

Objective share = 0.80. `aggregation: gated_weighted_sum`; a reverse-dependency step → `fail`
regardless of other credit (mirrors `ARCH-04` Example B).

## Confidence handling

Higher variance suite → `repeats: 10`. Judgment confidence is capped by the 0.20 rubric weight;
`plan_adequacy` labels come from expert consensus stored as data, not inferred at scoring time.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A standards violation (wrong approval count on a Tier-0/PCI
change) caps at `partial` even if the plan is otherwise strong.

## Model-independence notes

Ground truth is MCG standards and the dependency graph, identical across providers. A stronger
model may write more elegant prose, but the *scored* facts (risk tier, rollback, negative test,
sequencing) are provider-neutral, so BENCH-04 rewards enterprise-correct planning, not fluency.

## Failure modes / anti-gaming

- **Plan padding** — extra vacuous steps do not raise `required_elements_present` (substance
  checked, not count).
- **Rollback theater** — a rollback line that does not actually revert is caught by the judge +
  the requirement that it map to a real mechanism (feature flag / expand-contract).
- **Standards omission** — the most common real failure; explicitly gated.

## Example case

```json
{
  "id": "BC-0401",
  "suite": "BENCH-04",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Plan guest checkout for CHK-1421 (Tier-0)",
  "ecl_layer": "ARCH-06",
  "task_ref": "CHK-1421",
  "apps": ["APP-003","APP-012","APP-010","APP-015"],
  "difficulty": "hard",
  "inputs": {
    "trigger": { "type": "jira_story", "ref": "CHK-1421" },
    "context": { "ref": "CTX-0118", "includes": ["KN-045","KN-052","EXP-090"] },
    "standards": ["CANON-001#7"]
  },
  "ground_truth": {
    "type": "rubric_only",
    "must_include": ["EXP-090"],
    "expected": { "risk_tier": 0, "approvals": 2, "rollback": "feature_flag", "negative_test": true },
    "source": "PLAN-0072",
    "notes": "Tier-0 service APP-003 -> 2 approvals; APP-012 auth precedes APP-010 commit; no reverse deps."
  },
  "rubric": { "id": "RUBRIC-planning", "version": 2 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "required_elements_present", "kind": "objective", "weight": 0.25 },
      { "name": "standards_compliance", "kind": "objective", "weight": 0.25 },
      { "name": "dependency_sequencing", "kind": "objective", "weight": 0.20 },
      { "name": "negative_assertion_present", "kind": "objective", "weight": 0.10 },
      { "name": "plan_adequacy", "kind": "rubric", "weight": 0.20 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 10,
  "references": ["PLAN-0072","CHK-1421","EXP-090","APP-003","APP-012","APP-010","APP-015"]
}
```

## Relationship to ECL layers

Scores the planning responsibility of **Decision Intelligence** (`ARCH-06`, Stage 3). It consumes
context (BENCH-01) and experience (BENCH-03) and produces the `PLAN-###` that **Evaluation**
(`ARCH-04`) scores execution against — so a poor plan corrupts every downstream measurement, and
BENCH-04 is a gate on trusting the rest. Planning heuristics improved by the Learning Engine
(`ARCH-05`) should lift BENCH-04 over time (BENCH-09).
