#!/usr/bin/env python3
"""Deterministic generator for the EnterpriseSim learning corpus (Part 2).

Emits 100 complete Enterprise Worker executions as schema-valid WorkerExecutionBundle
JSON (corpus/executions/RUN-00NN.json), plus an accumulating experience store and an index.

Each bundle is the full ECL loop for one task:
  knowledge_retrieved -> context -> experience_retrieved -> decision -> plan ->
  execution -> evaluation -> reflection -> experience_update, with an evolving confidence.

Executions are grouped into recurring TASK FAMILIES. Within a family the Worker visibly
improves over time: later runs retrieve the experiences distilled from earlier runs,
reference prior runs, raise confidence, and score higher. RUN-0001/RUN-0002 reproduce the
canonical Foundation example loop (guest checkout) using the exact frozen example object ids.
"""
from __future__ import annotations
import json, os, random
from datetime import datetime, timedelta

random.seed(20260202)
H = os.path.expanduser("~/EnterpriseSim")
C = f"{H}/corpus"
os.makedirs(f"{C}/executions", exist_ok=True)
apps = {a["id"]: a for a in json.load(open(f"{H}/enterprise/registry/applications.json"))}
stories = json.load(open(f"{H}/enterprise/jira/jira_stories.json"))
by_app_story = {}
for s in stories:
    if s["type"] in ("story", "bug"):
        by_app_story.setdefault(s["app"], []).append(s["id"])
SV = "2020-12.v1"

def clamp(x, lo=0.0, hi=1.0):
    return round(max(lo, min(hi, x)), 2)

def sprint_start(s):
    return datetime(2026, 1, 5) + timedelta(days=(s - 1) * 14)

def ts(base, days=0, hours=0):
    return (base + timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

# family: (name, app, repo, knowledge ids, experience id+lesson, task_type, start_sprint, size)
FAMILIES = [
  ("guest-checkout", "APP-003", "mcg-checkout-service", ["KN-045", "KN-052"],
   ("EXP-090", "Guest checkout must not create a Loyalty (APP-015) account."), "feature", 1, 8),
  ("promo-cache", "APP-008", "mcg-promotions-engine", ["KN-063", "KN-304"],
   ("EXP-055", "Pricing/promotion changes during a promo window require a write-through APP-008 cache flush."), "bugfix", 4, 10),
  ("pricing-regional", "APP-007", "mcg-pricing-service", ["KN-100", "KN-303"],
   ("EXP-201", "Regional rounding rules must be validated per-currency before rollout."), "feature", 3, 8),
  ("payments-3ds", "APP-012", "mcg-payments-service", ["KN-052", "KN-258"],
   ("EXP-202", "3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions."), "feature", 5, 9),
  ("inventory-atp", "APP-010", "mcg-inventory-service", ["KN-307", "KN-210"],
   ("EXP-203", "Multi-warehouse ATP requires reservation locks to prevent oversell."), "bugfix", 6, 8),
  ("search-relevance", "APP-006", "mcg-search-service", ["KN-204", "KN-302"],
   ("EXP-204", "Relevance changes need offline judgment-set evaluation before shipping."), "feature", 2, 8),
  ("gateway-ratelimit", "APP-024", "mcg-api-gateway", ["KN-308", "KN-225"],
   ("EXP-205", "Rate-limit thresholds must be load-tested against realistic traffic shapes."), "hardening", 7, 7),
  ("order-saga", "APP-009", "mcg-oms", ["KN-209", "KN-307"],
   ("EXP-206", "Saga compensations must be idempotent and tested for partial failure."), "feature", 6, 8),
  ("cart-resilience", "APP-004", "mcg-cart-service", ["KN-300", "KN-207"],
   ("EXP-207", "Cart writes need optimistic concurrency plus Redis failover drills."), "hardening", 1, 7),
  ("returns-portal", "APP-021", "mcg-customer-portal", ["KN-310", "KN-201"],
   ("EXP-208", "Returns-eligibility rules need a golden-case suite across order states."), "feature", 8, 7),
  ("checkout-latency", "APP-003", "mcg-checkout-service", ["KN-313", "KN-229"],
   ("EXP-209", "Synchronous promo calls on the checkout path must be made async or cached."), "hardening", 9, 6),
  ("catalog-freshness", "APP-005", "mcg-catalog-service", ["KN-314", "KN-205"],
   ("EXP-210", "Catalog ingestion needs backpressure and data-platform outage handling."), "feature", 2, 7),
  ("test-authoring", "APP-006", "mcg-search-service", ["KN-204"],
   ("EXP-142", "Async webhook tests need deterministic clocks or they flake."), "test_authoring", 3, 7),
]
assert sum(f[7] for f in FAMILIES) == 100, sum(f[7] for f in FAMILIES)

WORKER = {"feature": "software-engineering-worker", "bugfix": "software-engineering-worker",
          "hardening": "reliability-worker", "incident_response": "incident-response-worker",
          "test_authoring": "qa-worker", "refactor": "software-engineering-worker"}

# ---- build run specs ------------------------------------------------------
specs = []  # each: dict with family, j, J, sprint, app, repo, kn, exp, ttype
for (name, app, repo, kn, exp, ttype, start, size) in FAMILIES:
    for j in range(size):
        sp = min(13, start + j)  # advance ~1 sprint per iteration, cap 13
        specs.append({"family": name, "j": j, "J": size, "sprint": sp, "app": app,
                      "repo": repo, "kn": kn, "exp": exp, "ttype": ttype})

# assign RUN ids: anchors are guest-checkout j0 (RUN-0001) and j1 (RUN-0002)
anchor0 = next(s for s in specs if s["family"] == "guest-checkout" and s["j"] == 0)
anchor1 = next(s for s in specs if s["family"] == "guest-checkout" and s["j"] == 1)
anchor0["run_id"] = "RUN-0001"; anchor1["run_id"] = "RUN-0002"
rest = [s for s in specs if "run_id" not in s]
rest.sort(key=lambda s: (s["sprint"], s["family"], s["j"]))
n = 3
for s in rest:
    s["run_id"] = f"RUN-{n:04d}"; n += 1
# map (family,j) -> run_id for prior_executions
famseq = {}
for s in specs:
    famseq.setdefault(s["family"], {})[s["j"]] = s["run_id"]

experience_store = {}   # exp_id -> ExperienceObject (accumulated)
bundles_by_run = {}

def pick_story(app, ttype):
    pool = by_app_story.get(app) or by_app_story.get("APP-003")
    return random.choice(pool)

def prov(src, kind, reason, score):
    return {"source": src, "kind": kind, "reason": reason, "score": clamp(score)}

def build_anchor_run1():
    base = sprint_start(1)
    ctx = {"id": "CTX-0091", "schema_version": SV, "created_at": ts(base, 2, 10),
        "task": {"type": "jira_story", "ref": "CHK-1421", "app": "APP-003", "repo": "mcg-checkout-service"},
        "intent_ref": "PLAN-0051", "model_budget": {"window_tokens": 200000, "reserved_output": 8000},
        "included": [prov("KN-052", "knowledge", "idempotency requirement for order placement", 0.87)],
        "excluded": [prov("KN-045", "knowledge", "checkout domain rules (incl. no-loyalty invariant) dropped for budget", 0.63)],
        "coverage_confidence": 0.58, "signals": {"hit_ratio": 0.55, "budget_utilization": 0.72, "staleness_index": 0.1}}
    plan = {"id": "PLAN-0051", "schema_version": SV, "created_at": ts(base, 2, 11), "task": "CHK-1421",
        "app": "APP-003", "intent": "Implement guest checkout end to end.",
        "success_criteria": ["Guest can place an order end to end.", "Idempotency preserved (KN-052)."],
        "steps": [{"n": 1, "action": "implement guest order path", "tool": "repo"},
                  {"n": 2, "action": "run unit + contract tests", "tool": "ci", "expect": "TR pass"},
                  {"n": 3, "action": "open PR", "tool": "github"}],
        "rollback": "Revert the guest-path change; no schema migration involved.",
        "risk_tier": 0, "routing": {"model_class": "high-reasoning", "reason": "Tier 0 checkout change"}}
    dec = {"id": "DEC-0001", "schema_version": SV, "created_at": ts(base, 2, 12), "plan": "PLAN-0051",
        "choice": "proceed", "rationale": "Context appeared sufficient; loyalty side-effect risk not surfaced (no prior experience).",
        "fused_confidence": 0.62, "inputs": {"context": 0.58, "knowledge": 0.7, "experience": 0.0, "evaluation": 0.6},
        "worker": "software-engineering-worker", "trace_seq": 1}
    exe = {"id": "EXE-0001", "schema_version": SV, "created_at": ts(base, 5, 14), "plan": "PLAN-0051",
        "step": 3, "tool": "github", "directives": {"open_pr": True},
        "artifacts": [{"id": "PR-0207", "schema_version": SV, "created_at": ts(base, 5, 14),
                       "artifact_type": "pull_request", "ref": "PR-0207", "uri": "mcg-checkout-service#207", "repo": "mcg-checkout-service"}],
        "status": "succeeded", "worker": "software-engineering-worker", "run_id": "RUN-0001"}
    ev = {"id": "EVAL-0044", "schema_version": SV, "created_at": ts(base, 6, 12), "execution": "PR-0207",
        "plan": "PLAN-0051", "task": "CHK-1421", "rubric": {"id": "RUBRIC-feature-change", "version": 3},
        "objective": [{"gate": "unit_tests", "result": "pass", "evidence": "TR-0440", "weight": 0.25},
                      {"gate": "coverage", "result": "pass", "value": 0.81, "threshold": 0.8, "evidence": "TR-0440", "weight": 0.15},
                      {"gate": "side_effect_check", "result": "fail", "note": "created APP-015 loyalty account for guests", "weight": 0.3},
                      {"gate": "dependency_rule", "result": "pass", "weight": 0.1}],
        "rubric_items": [{"item": "guest flow avoids unintended side effects", "result": "fail", "evidence": "post-incident review INC-2026-002", "judgment_confidence": 0.9}],
        "verdict": {"outcome": "fail", "score": 0.58, "outcome_confidence": 0.6, "judgment_confidence": 0.88},
        "regression_check": {"reintroduced_defect": False, "checked_against": []}}
    ref = {"id": "REF-0019", "schema_version": SV, "created_at": ts(base, 6, 16), "evaluation": "EVAL-0044",
        "execution": "PR-0207", "plan": "PLAN-0051",
        "what_happened": "Guest checkout implementation created a Loyalty (APP-015) account for every guest order, producing orphaned accounts. Tests passed because none asserted the negative case.",
        "root_cause": {"category": "missing_experience_and_test_gap",
            "detail": "No prior experience warned about the APP-003 -> APP-015 side effect, and the plan did not include a negative assertion. Context CTX-0091 did NOT include the loyalty domain rules (dropped for budget).",
            "confidence": 0.88},
        "lessons": [{"create_experience": "EXP-090"}],
        "policy_updates": [{"context": "for APP-003 feature changes, always retrieve APP-015 domain rules (raise priority)"},
                           {"planning": "feature-change plans must include negative-side-effect assertions"}],
        "loop_closed_by": "PR-0312"}
    exp = {"id": "EXP-090", "schema_version": SV, "created_at": ts(base, 6, 16),
        "title": "Guest carts must not create loyalty accounts",
        "situation": {"task_type": "feature_change", "apps": ["APP-003", "APP-015"], "failure_class": "unintended_side_effect"},
        "lesson": "When implementing guest flows in Checkout (APP-003), ensure no code path provisions a Loyalty (APP-015) account. A prior change created orphaned loyalty accounts for guests, triggering a data-cleanup incident.",
        "evidence": {"origin_execution": "PR-0207", "evaluation": "EVAL-0044", "reflection": "REF-0019"},
        "value": {"application_frequency": 0, "outcome_lift": 0.0, "corroboration": "weak", "contradiction_rate": 0.0},
        "status": "captured"}
    experience_store["EXP-090"] = exp
    return {"run_id": "RUN-0001", "schema_version": SV, "created_at": ts(base, 2, 10),
        "worker": "software-engineering-worker",
        "task": {"type": "feature", "ref": "CHK-1421", "app": "APP-003", "repo": "mcg-checkout-service", "sprint": 1, "family": "guest-checkout"},
        "knowledge_retrieved": ["KN-045", "KN-052"], "experience_retrieved": [], "prior_executions": [],
        "context": ctx, "decision": dec, "plan": plan, "execution": exe, "evaluation": ev, "reflection": ref,
        "experience_update": {"action": "created", "experience": "EXP-090",
            "delta": {"reason": "distilled from the orphaned-loyalty failure (INC-2026-002)"}},
        "confidence": {"context_coverage": 0.58, "knowledge_authority": 0.7, "experience_applicability": 0.0,
                       "evaluation_outcome": 0.58, "evaluation_judgment": 0.88, "fused": 0.55},
        "outcome": "fail"}

def build_anchor_run2():
    base = sprint_start(1)
    ctx = {"id": "CTX-0118", "schema_version": SV, "created_at": ts(base, 7, 10),
        "task": {"type": "jira_story", "ref": "CHK-1421", "app": "APP-003", "repo": "mcg-checkout-service"},
        "intent_ref": "PLAN-0072", "model_budget": {"window_tokens": 200000, "reserved_output": 8000},
        "included": [prov("KN-045", "knowledge", "defines order-placement invariants", 0.94),
                     prov("KN-052", "knowledge", "guest orders need idempotency keys", 0.88),
                     prov("EXP-090", "experience", "prior regression on APP-015", 0.91)],
        "excluded": [prov("KN-047", "knowledge", "dropped for budget; flagged", 0.61)],
        "coverage_confidence": 0.86, "signals": {"hit_ratio": 0.83, "budget_utilization": 0.41, "staleness_index": 0.12}}
    plan = {"id": "PLAN-0072", "schema_version": SV, "created_at": ts(base, 7, 11), "task": "CHK-1421",
        "app": "APP-003", "intent": "Add guest checkout without creating a Loyalty (APP-015) account.",
        "success_criteria": ["Guest can place an order end to end.", "No APP-015 account created for guests (negative test).", "Idempotency preserved (KN-052)."],
        "steps": [{"n": 1, "action": "read PlaceOrder.java + guest-flow tests", "tool": "repo"},
                  {"n": 2, "action": "implement guest path; guard APP-015 provisioning", "tool": "repo"},
                  {"n": 3, "action": "add GuestNoLoyaltyTest (negative assertion)", "tool": "repo"},
                  {"n": 4, "action": "run unit + contract tests", "tool": "ci", "expect": "TR-#### pass"},
                  {"n": 5, "action": "open PR with rollback plan", "tool": "github"}],
        "rollback": "Feature-flag guest checkout; disable flag to revert with no schema change.",
        "risk_tier": 0, "applied_experience": ["EXP-090"],
        "routing": {"model_class": "high-reasoning", "reason": "Tier 0 change with subtle side-effect risk"}}
    dec = {"id": "DEC-0002", "schema_version": SV, "created_at": ts(base, 7, 12), "plan": "PLAN-0072",
        "choice": "proceed", "rationale": "EXP-090 surfaced the loyalty side-effect risk; plan now includes a negative assertion. Fused confidence high.",
        "fused_confidence": 0.89, "inputs": {"context": 0.86, "knowledge": 0.92, "experience": 0.91, "evaluation": 0.9},
        "worker": "software-engineering-worker", "trace_seq": 1}
    exe = {"id": "EXE-0002", "schema_version": SV, "created_at": ts(base, 8, 14), "plan": "PLAN-0072",
        "step": 5, "tool": "github", "directives": {"open_pr": True, "feature_flag": "guest_checkout"},
        "artifacts": [{"id": "PR-0312", "schema_version": SV, "created_at": ts(base, 8, 15),
                       "artifact_type": "pull_request", "ref": "PR-0312", "uri": "mcg-checkout-service#312", "repo": "mcg-checkout-service"},
                      {"id": "TC-10001", "schema_version": SV, "created_at": ts(base, 8, 13),
                       "artifact_type": "test_run", "ref": "TR-0442", "uri": "testrail/runs/442"}],
        "status": "succeeded", "worker": "software-engineering-worker", "run_id": "RUN-0002"}
    ev = {"id": "EVAL-0061", "schema_version": SV, "created_at": ts(base, 8, 16), "execution": "PR-0312",
        "plan": "PLAN-0072", "task": "CHK-1421", "rubric": {"id": "RUBRIC-feature-change", "version": 3},
        "objective": [{"gate": "unit_tests", "result": "pass", "evidence": "TR-0442", "weight": 0.25},
                      {"gate": "coverage", "result": "pass", "value": 0.84, "threshold": 0.8, "evidence": "TR-0442", "weight": 0.15},
                      {"gate": "contract_tests", "result": "pass", "evidence": "TR-0443", "weight": 0.15},
                      {"gate": "dependency_rule", "result": "pass", "note": "no reverse dep APP-012->APP-003", "weight": 0.1}],
        "rubric_items": [{"item": "guest flow avoids APP-015 side effect", "result": "pass", "evidence": "test GuestNoLoyaltyTest", "judgment_confidence": 0.98},
                         {"item": "code clarity / maintainability", "result": "partial", "evidence": "reviewer notes", "judgment_confidence": 0.62}],
        "verdict": {"outcome": "pass", "score": 0.91, "outcome_confidence": 0.9, "judgment_confidence": 0.88},
        "regression_check": {"reintroduced_defect": False, "checked_against": ["EXP-090"]}}
    ref = {"id": "REF-1002", "schema_version": SV, "created_at": ts(base, 9, 10), "evaluation": "EVAL-0061",
        "execution": "PR-0312", "plan": "PLAN-0072",
        "what_happened": "Guest checkout shipped with a negative test asserting no loyalty account is created; the prior failure did not recur.",
        "root_cause": {"category": "missing_experience", "detail": "Applying EXP-090 and the updated retrieval policy closed the loop opened by REF-0019.", "confidence": 0.9},
        "lessons": [], "policy_updates": [], "loop_closed_by": "PR-0312"}
    experience_store["EXP-090"]["value"] = {"application_frequency": 1, "outcome_lift": 0.23, "corroboration": "moderate", "contradiction_rate": 0.0}
    experience_store["EXP-090"]["status"] = "reinforced"
    experience_store["EXP-090"]["evidence"]["prevented_regressions"] = ["PR-0312"]
    return {"run_id": "RUN-0002", "schema_version": SV, "created_at": ts(base, 7, 10),
        "worker": "software-engineering-worker",
        "task": {"type": "feature", "ref": "CHK-1421", "app": "APP-003", "repo": "mcg-checkout-service", "sprint": 1, "family": "guest-checkout"},
        "knowledge_retrieved": ["KN-045", "KN-052", "KN-063"], "experience_retrieved": ["EXP-090"], "prior_executions": ["RUN-0001"],
        "context": ctx, "decision": dec, "plan": plan, "execution": exe, "evaluation": ev, "reflection": ref,
        "experience_update": {"action": "reinforced", "experience": "EXP-090",
            "delta": {"application_frequency": 1, "outcome_lift": 0.23, "prevented_regressions": ["PR-0312"]}},
        "confidence": {"context_coverage": 0.86, "knowledge_authority": 0.92, "experience_applicability": 0.91,
                       "evaluation_outcome": 0.9, "evaluation_judgment": 0.88, "fused": 0.89},
        "outcome": "pass"}

bundles_by_run["RUN-0001"] = build_anchor_run1()
bundles_by_run["RUN-0002"] = build_anchor_run2()

# ---- generate the other 98 ------------------------------------------------
def build_generated(s):
    N = int(s["run_id"][4:])
    base = sprint_start(s["sprint"])
    app = s["app"]; fam = s["family"]; j = s["j"]; J = s["J"]
    maturity = j / (J - 1) if J > 1 else 1.0
    exp_id, exp_lesson = s["exp"]
    ttype = s["ttype"]
    story = pick_story(app, ttype)
    ref_id = story
    prior = [famseq[fam][j - 1]] if j > 0 else []
    # confidence evolution
    cov = clamp(0.55 + 0.38 * maturity + random.uniform(-0.05, 0.05))
    know = clamp(0.7 + 0.2 * maturity + random.uniform(-0.03, 0.03))
    expapp = 0.0 if j == 0 else clamp(0.6 + 0.33 * maturity + random.uniform(-0.04, 0.04))
    score = clamp(0.56 + 0.4 * maturity + random.uniform(-0.06, 0.06))
    jud = clamp(0.72 + 0.2 * maturity + random.uniform(-0.03, 0.03))
    if j == 0 and score < 0.7:
        outcome = "fail"
    elif score < 0.72:
        outcome = "partial"
    else:
        outcome = "pass"
    fused = clamp(0.2 * cov + 0.2 * know + 0.25 * expapp + 0.35 * score) if j > 0 else clamp(0.35 * cov + 0.35 * know + 0.3 * score)
    kn = list(s["kn"])
    exp_ret = [] if j == 0 else ([exp_id] + ([ "EXP-090"] if (fam != "guest-checkout" and random.random() < 0.15) else []))
    ctx_id = f"CTX-{1000 + N}"; plan_id = f"PLAN-{1000 + N}"; eval_id = f"EVAL-{1000 + N}"; ref_ref = f"REF-{1000 + N}"
    inc = [prov(k, "knowledge", f"relevant {fam} rule/doc", clamp(0.8 + 0.1 * maturity)) for k in kn]
    for e in exp_ret:
        inc.append(prov(e, "experience", f"prior {fam} lesson", clamp(0.75 + 0.15 * maturity)))
    excl = [] if maturity > 0.5 else [prov("KN-047", "knowledge", "lower-relevance doc dropped for budget", 0.4)]
    ctx = {"id": ctx_id, "schema_version": SV, "created_at": ts(base, 1, 9),
        "task": {"type": "jira_story", "ref": ref_id, "app": app, "repo": s["repo"]},
        "intent_ref": plan_id, "model_budget": {"window_tokens": 200000, "reserved_output": 8000},
        "included": inc, "excluded": excl, "coverage_confidence": cov,
        "signals": {"hit_ratio": clamp(0.55 + 0.35 * maturity), "budget_utilization": clamp(0.6 - 0.15 * maturity), "staleness_index": 0.1}}
    risk = apps[app]["criticality"]
    steps = [{"n": 1, "action": f"analyze {fam} change site", "tool": "repo"},
             {"n": 2, "action": f"implement {fam} change", "tool": "repo"}]
    if j > 0:
        steps.append({"n": 3, "action": f"add regression test for {exp_lesson[:40]}", "tool": "repo"})
    steps.append({"n": len(steps) + 1, "action": "run tests", "tool": "ci", "expect": "TR pass"})
    steps.append({"n": len(steps) + 1, "action": "open PR", "tool": "github"})
    plan = {"id": plan_id, "schema_version": SV, "created_at": ts(base, 1, 10), "task": ref_id, "app": app,
        "intent": f"{s['ttype'].capitalize()} for {fam}: {exp_lesson[:60]}",
        "success_criteria": ["Task acceptance criteria met.", "No regression of the known failure class."] + (["Applies prior lesson " + exp_id] if j > 0 else []),
        "steps": steps, "rollback": "Feature-flag or revert; expand-contract migration if schema touched.",
        "risk_tier": risk, "routing": {"model_class": "high-reasoning" if risk == 0 else "balanced", "reason": f"tier {risk} {fam} change"}}
    if j > 0:
        plan["applied_experience"] = [exp_id]
    dec_choice = "proceed" if outcome != "fail" else ("escalate" if risk == 0 and fused < 0.55 else "proceed")
    dec = {"id": f"DEC-{N:04d}", "schema_version": SV, "created_at": ts(base, 1, 11), "plan": plan_id,
        "choice": dec_choice,
        "rationale": (f"Applied {exp_id}; fused confidence adequate." if j > 0 else "Cold start for this family; limited prior experience."),
        "fused_confidence": fused, "inputs": {"context": cov, "knowledge": know, "experience": expapp, "evaluation": score},
        "worker": WORKER[ttype], "trace_seq": 1}
    artifact_ref = f"PR-{6000 + N}"
    if ttype == "test_authoring":
        art = {"id": f"TR-{7000 + N}", "schema_version": SV, "created_at": ts(base, 2, 14),
               "artifact_type": "test_run", "ref": f"TR-{7000 + N}", "uri": f"testrail/runs/{7000 + N}"}
    elif ttype == "incident_response":
        art = {"id": artifact_ref, "schema_version": SV, "created_at": ts(base, 2, 14),
               "artifact_type": "pull_request", "ref": artifact_ref, "uri": f"{s['repo']}#{6000 + N}", "repo": s["repo"]}
    else:
        art = {"id": artifact_ref, "schema_version": SV, "created_at": ts(base, 2, 14),
               "artifact_type": "pull_request", "ref": artifact_ref, "uri": f"{s['repo']}#{6000 + N}", "repo": s["repo"]}
    exe = {"id": f"EXE-{N:04d}", "schema_version": SV, "created_at": ts(base, 2, 14), "plan": plan_id,
        "step": len(steps), "tool": "github", "directives": {"open_pr": True},
        "artifacts": [art], "status": "succeeded" if outcome != "fail" else "partial",
        "worker": WORKER[ttype], "run_id": s["run_id"]}
    gates = [{"gate": "unit_tests", "result": "pass" if score > 0.6 else "fail", "evidence": f"TR-{7000 + N}", "weight": 0.3},
             {"gate": "coverage", "result": "pass" if score > 0.62 else "fail", "value": clamp(0.78 + 0.1 * maturity), "threshold": 0.8, "evidence": f"TR-{7000 + N}", "weight": 0.2},
             {"gate": "dependency_rule", "result": "pass", "weight": 0.2},
             {"gate": "security_scan", "result": "pass", "weight": 0.15}]
    if outcome == "fail":
        gates.append({"gate": "regression_check", "result": "fail", "note": f"{fam} failure class not yet guarded", "weight": 0.15})
    else:
        gates.append({"gate": "regression_check", "result": "pass", "weight": 0.15})
    ev = {"id": eval_id, "schema_version": SV, "created_at": ts(base, 3, 12), "execution": art["ref"],
        "plan": plan_id, "task": ref_id, "rubric": {"id": f"RUBRIC-{ttype}", "version": 2},
        "objective": gates,
        "rubric_items": [{"item": f"{fam} change is correct and maintainable", "result": outcome, "evidence": "reviewer notes", "judgment_confidence": jud}],
        "verdict": {"outcome": outcome, "score": score, "outcome_confidence": clamp(score + 0.02), "judgment_confidence": jud},
        "regression_check": {"reintroduced_defect": outcome == "fail" and j == 0, "checked_against": exp_ret}}
    # reflection
    if outcome == "fail":
        rc = {"category": "missing_experience" if j == 0 else "flawed_plan",
              "detail": f"The {fam} failure class was not guarded; distilling a lesson to prevent recurrence.", "confidence": clamp(0.75 + 0.1 * maturity)}
        lessons = [{"create_experience": exp_id}] if j == 0 else []
        pol = [{"context": f"raise retrieval priority of {fam} rules"}, {"planning": "add regression assertion for this failure class"}]
    else:
        rc = {"category": "missing_experience", "detail": f"Applying {exp_id} kept the {fam} failure class from recurring; loop closed.", "confidence": clamp(0.8 + 0.1 * maturity)}
        lessons = []
        pol = []
    ref = {"id": ref_ref, "schema_version": SV, "created_at": ts(base, 3, 16), "evaluation": eval_id,
        "execution": art["ref"], "plan": plan_id,
        "what_happened": (f"{fam} task {'failed the regression class and produced a new lesson' if outcome=='fail' else 'succeeded, applying accumulated experience'}."),
        "root_cause": rc, "lessons": lessons, "policy_updates": pol}
    if j > 0:
        ref["loop_closed_by"] = art["ref"]
    # experience update
    if j == 0:
        expobj = {"id": exp_id, "schema_version": SV, "created_at": ts(base, 3, 16), "title": exp_lesson[:60],
            "situation": {"task_type": ttype, "apps": [app], "failure_class": f"{fam}-regression"},
            "lesson": exp_lesson, "evidence": {"origin_execution": art["ref"], "evaluation": eval_id, "reflection": ref_ref},
            "value": {"application_frequency": 0, "outcome_lift": 0.0, "corroboration": "weak", "contradiction_rate": 0.0},
            "status": "captured"}
        experience_store[exp_id] = expobj
        eu = {"action": "created", "experience": exp_id, "delta": {"reason": f"distilled from first {fam} run"}}
    else:
        if exp_id in experience_store:
            e = experience_store[exp_id]
            e["value"]["application_frequency"] = e["value"].get("application_frequency", 0) + 1
            e["value"]["outcome_lift"] = round(min(0.4, e["value"].get("outcome_lift", 0.0) + 0.05), 2)
            e["value"]["corroboration"] = "strong" if e["value"]["application_frequency"] >= 3 else "moderate"
            e["status"] = "promotion_candidate" if e["value"]["application_frequency"] >= 3 else "reinforced"
            e.setdefault("evidence", {}).setdefault("prevented_regressions", [])
            if outcome == "pass":
                e["evidence"]["prevented_regressions"].append(art["ref"])
        eu = {"action": "reinforced", "experience": exp_id, "delta": {"application_frequency_inc": 1, "outcome": outcome}}
    return {"run_id": s["run_id"], "schema_version": SV, "created_at": ts(base, 1, 9), "worker": WORKER[ttype],
        "task": {"type": ttype, "ref": ref_id, "app": app, "repo": s["repo"], "sprint": s["sprint"], "family": fam},
        "knowledge_retrieved": kn, "experience_retrieved": exp_ret, "prior_executions": prior,
        "context": ctx, "decision": dec, "plan": plan, "execution": exe, "evaluation": ev, "reflection": ref,
        "experience_update": eu,
        "confidence": {"context_coverage": cov, "knowledge_authority": know, "experience_applicability": expapp,
                       "evaluation_outcome": score, "evaluation_judgment": jud, "fused": fused},
        "outcome": outcome}

# generate in RUN-id order so experience_store accumulates causally
for s in sorted(rest, key=lambda s: int(s["run_id"][4:])):
    bundles_by_run[s["run_id"]] = build_generated(s)

# ---- write ----------------------------------------------------------------
def strip_none(o):
    if isinstance(o, dict): return {k: strip_none(v) for k, v in o.items() if v is not None}
    if isinstance(o, list): return [strip_none(x) for x in o]
    return o

index = []
for rid in sorted(bundles_by_run, key=lambda r: int(r[4:])):
    b = strip_none(bundles_by_run[rid])
    with open(f"{C}/executions/{rid}.json", "w") as f:
        json.dump(b, f, indent=2); f.write("\n")
    index.append({"run_id": rid, "family": b["task"]["family"], "task": b["task"]["ref"],
                  "app": b["task"]["app"], "sprint": b["task"]["sprint"], "outcome": b["outcome"],
                  "fused_confidence": b["confidence"]["fused"], "score": b["evaluation"]["verdict"]["score"],
                  "experience_update": b["experience_update"]["action"], "experience": b["experience_update"]["experience"],
                  "prior_executions": b["prior_executions"]})
with open(f"{C}/index.json", "w") as f:
    json.dump(index, f, indent=2); f.write("\n")
store = [strip_none(experience_store[k]) for k in sorted(experience_store)]
with open(f"{C}/experience_store.json", "w") as f:
    json.dump(store, f, indent=2); f.write("\n")

print(f"executions={len(bundles_by_run)} experiences={len(experience_store)}")
# quick improvement check per family
from statistics import mean
fam_scores = {}
for b in bundles_by_run.values():
    fam_scores.setdefault(b["task"]["family"], []).append((b["task"]["sprint"], b["confidence"]["fused"]))
print("families:", len(fam_scores))
