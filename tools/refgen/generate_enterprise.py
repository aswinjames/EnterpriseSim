#!/usr/bin/env python3
"""Deterministic generator for the EnterpriseSim reference operational datasets.

Reads enterprise/registry/* and emits internally-consistent, schema-valid datasets:
  jira/jira_stories.json        (150 stories/epics/bugs/spikes/hotfixes)
  pull-requests/pull_requests.json (50 PRs)
  commits/commits.json          (500 commit-metadata records)
  tests/test_cases.json         (100 automated test cases)
  incidents/incidents.json      (15 production incidents)
and enriches registry/releases.json with included_stories / included_prs / related_incidents.

Deterministic (seeded) for reproducibility (ADR-0037). Anchors the canonical Foundation
artifacts so the enterprise and the ECL examples are one world: CHK-1421, PAY-980,
PR-0207/PR-0312, GuestNoLoyaltyTest, INC-2026-007/011/018.
"""
from __future__ import annotations
import json, os, random, hashlib
from datetime import datetime, timedelta

random.seed(20260101)
H = os.path.expanduser("~/EnterpriseSim/enterprise")
apps = {a["id"]: a for a in json.load(open(f"{H}/registry/applications.json"))}
releases = json.load(open(f"{H}/registry/releases.json"))
SV = "2020-12.v1"

# Jira project key per focal app
KEY = {"APP-001": "STF", "APP-021": "POR", "APP-003": "CHK", "APP-004": "CRT",
       "APP-005": "CAT", "APP-006": "SRCH", "APP-007": "PRC", "APP-008": "PRM",
       "APP-009": "OMS", "APP-010": "INV", "APP-012": "PAY", "APP-024": "GW"}
# starting issue numbers so canonical keys (CHK-1421, PAY-980) fall in range
BASE = {"STF": 810, "POR": 620, "CHK": 1400, "CRT": 540, "CAT": 930, "SRCH": 720,
        "PRC": 1120, "PRM": 1010, "OMS": 1310, "INV": 1230, "PAY": 970, "GW": 430}

# Realistic per-app feature phrase banks (feature verbs + domain nouns) -> varied titles
FEATURES = {
    "APP-001": ["server-side render product detail pages", "lazy-load below-the-fold imagery",
                "add A/B harness for hero layout", "hydrate cart badge without full reload",
                "improve Core Web Vitals on category pages", "localize currency and units per region"],
    "APP-021": ["self-service return initiation", "order timeline view", "saved payment methods UI",
                "address book management", "download invoice as PDF", "loyalty points balance widget"],
    "APP-003": ["support guest checkout", "add idempotency keys to order placement",
                "reduce p99 checkout latency", "handle partial payment authorization",
                "graceful degradation when promotions unavailable", "split-tender payment support"],
    "APP-004": ["Redis failover for cart state", "merge guest cart on sign-in",
                "cart-level price preview", "expire abandoned carts", "cap line-item quantity",
                "optimistic concurrency on cart writes"],
    "APP-005": ["sub-minute catalog reindex", "variant-level availability flags",
                "bulk offer ingestion from data platform", "soft-delete discontinued SKUs",
                "category taxonomy versioning", "product enrichment webhook"],
    "APP-006": ["hybrid lexical+semantic ranking", "typo-tolerant query parsing",
                "personalized recommendations sidebar", "faceted filter performance",
                "reduce reindex propagation lag", "synonym dictionary management"],
    "APP-007": ["regional price resolution", "price-consistency verification job",
                "markdown scheduling", "currency rounding rules", "price change audit trail",
                "cost-plus margin guardrails"],
    "APP-008": ["stacked promotion rules v2", "promo-cache TTL controls", "write-through promo cache",
                "coupon eligibility engine", "budget caps per campaign", "exclusion-list handling"],
    "APP-009": ["saga-based fulfillment orchestration", "order state machine hardening",
                "backorder handling", "partial shipment support", "cancellation and refund flow",
                "idempotent event consumption"],
    "APP-010": ["available-to-promise reservation fix", "oversell protection",
                "multi-warehouse allocation", "stock reconciliation job", "reservation TTL",
                "low-stock event publishing"],
    "APP-012": ["3DS2 challenge flow", "PSP failover routing", "retry-storm protection",
                "tokenized card vault", "refund idempotency", "partial capture support"],
    "APP-024": ["token-bucket rate limiting", "edge OIDC verification", "request coalescing",
                "circuit breaker per upstream", "load-shedding under pressure", "canary routing"],
}
AUTHORS = ["a.rivera", "j.okafor", "l.schmidt", "m.tanaka", "s.popov", "n.almeida",
           "d.oconnor", "r.gupta", "e.johansson", "c.mendez", "t.nguyen", "b.kowalski"]

def dt(base, days=0, hours=0):
    return (base + timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

def sprint_start(s):  # sprint 1 starts 2026-01-05 (Mon); 2-week sprints
    return datetime(2026, 1, 5) + timedelta(days=(s - 1) * 14)

def sha(*parts):
    return hashlib.sha1(("|".join(map(str, parts))).encode()).hexdigest()[:10]

# sprint -> release id (sprints 1..10 map to REL-2026-001..010; 11..13 none)
def rel_for(s):
    return f"REL-2026-{s:03d}" if 1 <= s <= 10 else None

# sprint -> primary apps (drawn from release themes) so work clusters thematically
PRIMARY = {1: ["APP-003", "APP-004"], 2: ["APP-005", "APP-006"], 3: ["APP-007"],
           4: ["APP-008", "APP-007"], 5: ["APP-012"], 6: ["APP-009", "APP-010"],
           7: ["APP-024"], 8: ["APP-021", "APP-009"], 9: ["APP-001", "APP-003", "APP-024"],
           10: ["APP-003", "APP-008"], 11: ["APP-006", "APP-005"], 12: ["APP-012", "APP-009"],
           13: ["APP-001", "APP-021"]}

counters = {k: BASE[k] for k in BASE}
def next_key(app, reserved):
    k = KEY[app]
    counters[k] += random.randint(1, 4)
    while f"{k}-{counters[k]}" in reserved:
        counters[k] += 1
    return f"{k}-{counters[k]}"

stories = []
reserved_keys = {"CHK-1421", "PAY-980"}

# ---- anchor stories -------------------------------------------------------
s1 = sprint_start(1)
stories.append({
    "id": "CHK-1421", "schema_version": SV, "created_at": dt(s1, 1, 9), "type": "story",
    "title": "Support guest checkout in the Checkout Service",
    "description": "Allow unauthenticated buyers to place an order end to end. Guest checkout MUST NOT create a Loyalty (APP-015) account, and MUST preserve idempotency (KN-052).",
    "app": "APP-003", "repo": "mcg-checkout-service", "team": "TEAM-004", "sprint": 1,
    "points": 8, "status": "done", "priority": "P1", "resolved_at": dt(s1, 9, 16),
    "release": "REL-2026-001", "labels": ["guest-checkout", "conversion"],
    "prs": ["PR-0207", "PR-0312"]})
s5 = sprint_start(5)
stories.append({
    "id": "PAY-980", "schema_version": SV, "created_at": dt(s5, 1, 10), "type": "story",
    "title": "Implement 3DS2 challenge flow for card authorization",
    "description": "Add Strong Customer Authentication (3DS2) challenge handling to Payments within the PCI boundary (APP-012).",
    "app": "APP-012", "repo": "mcg-payments-service", "team": "TEAM-009", "sprint": 5,
    "points": 13, "status": "done", "priority": "P0", "resolved_at": dt(s5, 11, 15),
    "release": "REL-2026-005", "labels": ["pci", "3ds", "sca"], "prs": ["PR-0503"]})

# ---- epics (one per sprint per primary app) -------------------------------
epics = {}
for s in range(1, 14):
    for app in PRIMARY[s][:1]:
        ek = next_key(app, reserved_keys); reserved_keys.add(ek)
        base = sprint_start(s)
        feat = FEATURES[app][ (s) % len(FEATURES[app]) ]
        epics[(s, app)] = ek
        stories.append({
            "id": ek, "schema_version": SV, "created_at": dt(base, 0, 8), "type": "epic",
            "title": f"[Epic] {feat.capitalize()} initiative",
            "description": f"Sprint {s} initiative for {apps[app]['name']} ({app}).",
            "app": app, "repo": apps[app]["repository"], "team": apps[app]["owner_team"],
            "sprint": s, "points": 13, "status": "done", "priority": "P1",
            "resolved_at": dt(base, 12, 17), "release": rel_for(s), "labels": ["epic"]})

# ---- fill to 150 stories --------------------------------------------------
TYPE_W = [("story", 0.6), ("task", 0.15), ("bug", 0.15), ("spike", 0.1)]
def weighted_type():
    r = random.random(); acc = 0
    for t, w in TYPE_W:
        acc += w
        if r <= acc: return t
    return "story"

while len(stories) < 150:
    s = random.randint(1, 13)
    app = random.choice(PRIMARY[s] + [random.choice(list(KEY))])
    key = next_key(app, reserved_keys); reserved_keys.add(key)
    base = sprint_start(s)
    off = random.randint(0, 11)
    feat = random.choice(FEATURES[app])
    ttype = weighted_type()
    title = {"story": feat.capitalize(),
             "task": f"Refactor: {feat}",
             "bug": f"Fix incorrect behavior in {feat}",
             "spike": f"Investigate approach for {feat}"}[ttype]
    stories.append({
        "id": key, "schema_version": SV, "created_at": dt(base, off, 9), "type": ttype,
        "title": title,
        "description": f"{title} for {apps[app]['name']} ({app}).",
        "app": app, "repo": apps[app]["repository"], "team": apps[app]["owner_team"],
        "sprint": s, "points": random.choice([1, 2, 3, 5, 8]),
        "status": "done", "priority": random.choice(["P1", "P2", "P2", "P3"]),
        "resolved_at": dt(base, min(off + random.randint(1, 5), 13), 16),
        "epic": epics.get((s, app)), "release": rel_for(s),
        "labels": random.sample(["perf", "reliability", "ux", "tech-debt", "observability", "security"], k=random.randint(1, 2))})

story_by_id = {s["id"]: s for s in stories}

# ---- pull requests (50, incl. anchors) ------------------------------------
prs = []
used_pr_nums = {207, 312, 503}
def new_pr_num():
    n = random.randint(100, 640)
    while n in used_pr_nums:
        n = random.randint(100, 640)
    used_pr_nums.add(n); return n

# anchor PRs
prs.append({"id": "PR-0207", "schema_version": SV, "created_at": dt(s1, 3, 10), "repo": "mcg-checkout-service",
    "native_number": 207, "title": "CHK-1421: initial guest checkout implementation",
    "app": "APP-003", "team": "TEAM-004", "author": "a.rivera", "story": "CHK-1421",
    "branch": "feature/CHK-1421-guest-checkout", "base": "main", "state": "merged",
    "merged_at": dt(s1, 5, 14), "commits": [], "additions": 640, "deletions": 90, "changed_files": 14,
    "reviews": 2, "approvals": 2, "risk_tier": 0,
    "checks": {"ci": "passed", "coverage": 0.81, "test_run": "TR-0440", "security_scan": "passed"},
    "release": "REL-2026-001", "is_hotfix": False, "labels": ["guest-checkout"]})
prs.append({"id": "PR-0312", "schema_version": SV, "created_at": dt(s1, 8, 9), "repo": "mcg-checkout-service",
    "native_number": 312, "title": "CHK-1421: guard against loyalty account creation for guests",
    "app": "APP-003", "team": "TEAM-004", "author": "a.rivera", "story": "CHK-1421",
    "branch": "hotfix/INC-2026-002-guest-loyalty", "base": "main", "state": "merged",
    "merged_at": dt(s1, 9, 15), "commits": [], "additions": 120, "deletions": 22, "changed_files": 5,
    "reviews": 2, "approvals": 2, "risk_tier": 0,
    "checks": {"ci": "passed", "coverage": 0.84, "test_run": "TR-0442", "security_scan": "passed"},
    "release": "REL-2026-001", "is_hotfix": True, "labels": ["guest-checkout", "hotfix"]})
prs.append({"id": "PR-0503", "schema_version": SV, "created_at": dt(s5, 4, 10), "repo": "mcg-payments-service",
    "native_number": 503, "title": "PAY-980: 3DS2 challenge flow",
    "app": "APP-012", "team": "TEAM-009", "author": "l.schmidt", "story": "PAY-980",
    "branch": "feature/PAY-980-3ds2", "base": "main", "state": "merged",
    "merged_at": dt(s5, 10, 15), "commits": [], "additions": 910, "deletions": 140, "changed_files": 22,
    "reviews": 2, "approvals": 2, "risk_tier": 0,
    "checks": {"ci": "passed", "coverage": 0.86, "test_run": "TR-0512", "security_scan": "passed"},
    "release": "REL-2026-005", "is_hotfix": False, "labels": ["pci", "3ds"]})

# remaining PRs from code-bearing stories
code_stories = [s for s in stories if s["type"] in ("story", "bug", "task") and s["id"] not in ("CHK-1421", "PAY-980")]
random.shuffle(code_stories)
pr_seq = 1000
for st in code_stories:
    if len(prs) >= 50:
        break
    num = new_pr_num()
    base = datetime.strptime(st["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    author = random.choice(AUTHORS)
    cov = round(random.uniform(0.78, 0.93), 2)
    risk = apps[st["app"]]["criticality"]
    prid = f"PR-{num:04d}"
    prs.append({"id": prid, "schema_version": SV, "created_at": dt(base, 1, 10), "repo": st["repo"],
        "native_number": num, "title": f"{st['id']}: {st['title'][:70]}",
        "app": st["app"], "team": st["team"], "author": author, "story": st["id"],
        "branch": f"feature/{st['id']}-{st['title'].split()[0].lower()}", "base": "main", "state": "merged",
        "merged_at": dt(base, random.randint(2, 5), 15), "commits": [],
        "additions": random.randint(40, 900), "deletions": random.randint(5, 200),
        "changed_files": random.randint(2, 20), "reviews": 1 if risk >= 2 else 2,
        "approvals": 2 if risk == 0 else 1, "risk_tier": risk,
        "checks": {"ci": "passed", "coverage": cov, "security_scan": "passed"},
        "release": st.get("release"), "is_hotfix": False,
        "labels": st.get("labels", [])[:2]})
    st.setdefault("prs", []).append(prid)

pr_by_id = {p["id"]: p for p in prs}

# ---- commits (500 across PRs) ---------------------------------------------
commits = []
COMMIT_VERBS = ["implement", "add tests for", "refactor", "fix edge case in", "wire up",
                "handle error path in", "add metrics to", "document", "address review on", "tidy"]
per_pr = {}
# base allocation: distribute 500 commits over 50 PRs
counts = [random.randint(4, 14) for _ in prs]
scale = 500 / sum(counts)
counts = [max(3, round(c * scale)) for c in counts]
# adjust to exactly 500
while sum(counts) > 500: counts[counts.index(max(counts))] -= 1
while sum(counts) < 500: counts[counts.index(min(counts))] += 1
for p, n in zip(prs, counts):
    base = datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    for i in range(n):
        cid = sha(p["id"], i)
        verb = COMMIT_VERBS[i % len(COMMIT_VERBS)]
        msg = f"{p['story']}: {verb} {p['title'].split(': ',1)[-1][:50]}".strip()
        commits.append({"id": cid, "schema_version": SV, "created_at": dt(base, 0, i),
            "repo": p["repo"], "pr": p["id"], "story": p["story"], "author": p["author"],
            "message": msg, "committed_at": dt(base, i // 4, (i % 4) * 3),
            "additions": random.randint(3, 120), "deletions": random.randint(0, 40),
            "files_changed": random.randint(1, 6)})
        p["commits"].append(cid)

# ---- test cases (100) -----------------------------------------------------
tests = []
TS = {app: f"TS-{100 + i:03d}" for i, app in enumerate(KEY)}
tc_num = 10000
# anchor: GuestNoLoyaltyTest
tests.append({"id": "TC-10001", "schema_version": SV, "created_at": dt(s1, 8, 12),
    "title": "GuestNoLoyaltyTest: guest checkout does not create a loyalty account",
    "app": "APP-003", "repo": "mcg-checkout-service", "suite": TS["APP-003"], "type": "unit",
    "status": "active", "priority": "P0", "owner_team": "TEAM-004", "automated": True,
    "related_story": "CHK-1421", "critical_journey": "guest-checkout"})
TYPES = ["unit", "unit", "unit", "contract", "integration", "e2e", "performance", "security"]
apps_cycle = list(KEY)
i = 0
while len(tests) < 100:
    app = apps_cycle[i % len(apps_cycle)]; i += 1
    tc_num += 1
    ttype = random.choice(TYPES)
    feat = random.choice(FEATURES[app])
    tests.append({"id": f"TC-{tc_num}", "schema_version": SV, "created_at": dt(sprint_start(random.randint(1, 13)), random.randint(0, 12), 11),
        "title": f"{ttype.capitalize()} - {feat}", "app": app, "repo": apps[app]["repository"],
        "suite": TS[app], "type": ttype, "status": "active" if random.random() > 0.03 else "quarantined",
        "priority": random.choice(["P0", "P1", "P1", "P2"]), "owner_team": apps[app]["owner_team"],
        "automated": True})

# ---- incidents (15, anchored IDs incl. 007/011/018) -----------------------
def isprint(s): return sprint_start(s)
incidents = [
  {"id": "INC-2026-001", "sev": "Sev2", "apps": ["APP-004"], "s": 1, "cat": "capacity",
   "title": "Cart Redis primary failover caused elevated errors",
   "summary": "A Redis primary failover in cart caused a 9-minute spike in cart write errors before replica promotion completed.",
   "trigger": "organic", "regions": ["NA"], "rel": "REL-2026-001"},
  {"id": "INC-2026-002", "sev": "Sev2", "apps": ["APP-003", "APP-015"], "s": 1, "cat": "code_regression",
   "title": "Guest checkout created orphaned loyalty accounts",
   "summary": "PR-0207 provisioned a Loyalty (APP-015) account for every guest order, creating orphaned accounts. Fixed by hotfix PR-0312.",
   "trigger": "PR-0207", "regions": ["NA", "EU"], "rel": "REL-2026-001",
   "hotfix_pr": "PR-0312", "hotfix_story": "CHK-1421"},
  {"id": "INC-2026-003", "sev": "Sev3", "apps": ["APP-006"], "s": 2, "cat": "data_issue",
   "title": "Search reindex lag surfaced stale prices in results",
   "summary": "Catalog-to-index propagation lag briefly showed stale prices in search results.",
   "trigger": "REL-2026-002", "regions": ["NA"], "rel": "REL-2026-002"},
  {"id": "INC-2026-004", "sev": "Sev2", "apps": ["APP-007"], "s": 3, "cat": "config_change",
   "title": "Regional price rule misconfiguration in APAC",
   "summary": "A regional rounding rule misconfiguration produced off-by-one currency rounding in APAC for 22 minutes.",
   "trigger": "REL-2026-003", "regions": ["APAC"], "rel": "REL-2026-003"},
  {"id": "INC-2026-007", "sev": "Sev1", "apps": ["APP-008", "APP-007", "APP-003"], "s": 4, "cat": "cache_staleness",
   "title": "Promotion-window price change did not invalidate promo cache",
   "summary": "A promotion-window pricing change was not reflected because the promotions cache (APP-008) was not invalidated, causing incorrect cart totals at checkout.",
   "trigger": "REL-2026-004", "regions": ["NA", "EU"], "rel": "REL-2026-004"},
  {"id": "INC-2026-009", "sev": "Sev2", "apps": ["APP-012"], "s": 5, "cat": "third_party",
   "title": "Primary PSP degraded; authorization latency spiked",
   "summary": "The primary payment service provider degraded; authorization p99 spiked until failover routing engaged.",
   "trigger": "organic", "regions": ["NA", "LATAM"], "rel": "REL-2026-005"},
  {"id": "INC-2026-011", "sev": "Sev2", "apps": ["APP-008", "APP-003"], "s": 6, "cat": "cache_staleness",
   "title": "Promo cache staleness recurrence during flash sale",
   "summary": "A recurrence of promo-cache staleness (cf. INC-2026-007) during a flash sale produced brief total mismatches.",
   "trigger": "organic", "regions": ["NA"], "rel": "REL-2026-006"},
  {"id": "INC-2026-012", "sev": "Sev2", "apps": ["APP-010", "APP-009"], "s": 6, "cat": "data_issue",
   "title": "ATP oversell on multi-warehouse SKUs",
   "summary": "A reservation race across warehouses briefly allowed oversell on high-demand SKUs.",
   "trigger": "REL-2026-006", "regions": ["NA"], "rel": "REL-2026-006"},
  {"id": "INC-2026-013", "sev": "Sev3", "apps": ["APP-024"], "s": 7, "cat": "config_change",
   "title": "Rate-limit threshold too aggressive after rollout",
   "summary": "A too-aggressive token-bucket threshold rejected legitimate traffic for 14 minutes after rollout.",
   "trigger": "REL-2026-007", "regions": ["EU"], "rel": "REL-2026-007"},
  {"id": "INC-2026-014", "sev": "Sev2", "apps": ["APP-024", "APP-014"], "s": 7, "cat": "deployment",
   "title": "Edge OIDC verification rejected valid tokens",
   "summary": "A clock-skew tolerance bug in edge OIDC verification rejected valid tokens for a subset of users.",
   "trigger": "REL-2026-007", "regions": ["NA", "EU"], "rel": "REL-2026-007"},
  {"id": "INC-2026-015", "sev": "Sev3", "apps": ["APP-021"], "s": 8, "cat": "code_regression",
   "title": "Self-service returns showed incorrect eligibility",
   "summary": "A returns-eligibility rule regression showed some delivered orders as ineligible.",
   "trigger": "REL-2026-008", "regions": ["NA"], "rel": "REL-2026-008"},
  {"id": "INC-2026-016", "sev": "Sev2", "apps": ["APP-001", "APP-024"], "s": 9, "cat": "capacity",
   "title": "Storefront latency degradation under load test",
   "summary": "A pre-peak load test revealed origin saturation; load-shedding at the edge was tuned in response.",
   "trigger": "organic", "regions": ["NA"], "rel": "REL-2026-009"},
  {"id": "INC-2026-018", "sev": "Sev1", "apps": ["APP-008", "APP-007", "APP-003"], "s": 10, "cat": "cache_staleness",
   "title": "Third promo-cache staleness incident triggers systemic fix",
   "summary": "The third promo-cache staleness incident (cf. INC-2026-007, INC-2026-011) drove a systemic write-through cache fix and a standing pre-release check.",
   "trigger": "organic", "regions": ["NA", "EU"], "rel": "REL-2026-010"},
  {"id": "INC-2026-019", "sev": "Sev3", "apps": ["APP-003"], "s": 10, "cat": "capacity",
   "title": "Checkout p99 latency regression from synchronous promo call",
   "summary": "A synchronous promotions call on the checkout path regressed p99 latency until made asynchronous.",
   "trigger": "REL-2026-010", "regions": ["NA"], "rel": "REL-2026-010"},
  {"id": "INC-2026-021", "sev": "Sev3", "apps": ["APP-005"], "s": 12, "cat": "dependency_failure",
   "title": "Catalog ingestion stalled on data-platform outage",
   "summary": "A brief data-platform (APP-020) outage stalled catalog offer ingestion; caught up after recovery.",
   "trigger": "organic", "regions": ["NA", "EU", "APAC"], "rel": None},
]
pm_num = 300
incident_records = []
for inc in incidents:
    base = isprint(inc["s"])
    det = dt(base, random.randint(1, 11), random.randint(0, 20))
    dur = {"Sev1": random.randint(35, 120), "Sev2": random.randint(15, 60),
           "Sev3": random.randint(8, 30), "Sev4": random.randint(5, 15)}[inc["sev"]]
    res = dt(datetime.strptime(det, "%Y-%m-%dT%H:%M:%SZ"), 0, 0)
    resolved = (datetime.strptime(det, "%Y-%m-%dT%H:%M:%SZ") + timedelta(minutes=dur)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pm = f"KN-{pm_num}"; pm_num += 1
    teams = sorted({apps[a]["owner_team"] for a in inc["apps"] if a in apps})
    rec = {"id": inc["id"], "schema_version": SV, "created_at": det, "title": inc["title"],
           "severity": inc["sev"], "apps": inc["apps"], "teams": teams or ["TEAM-032"],
           "detected_at": det, "resolved_at": resolved, "duration_min": dur,
           "summary": inc["summary"], "trigger": inc["trigger"], "root_cause_category": inc["cat"],
           "impacted_regions": inc["regions"], "postmortem": pm, "status": "resolved"}
    if inc.get("rel"): rec["related_release"] = inc["rel"]
    if inc.get("hotfix_pr"): rec["hotfix_pr"] = inc["hotfix_pr"]
    if inc.get("hotfix_story"): rec["hotfix_story"] = inc["hotfix_story"]
    incident_records.append(rec)

# ---- enrich releases with contents ----------------------------------------
for r in releases:
    rid = r["id"]
    r["included_stories"] = sorted([s["id"] for s in stories if s.get("release") == rid and s["type"] != "epic"])[:20]
    r["included_prs"] = sorted([p["id"] for p in prs if p.get("release") == rid])
    ri = sorted([inc["id"] for inc in incident_records if inc.get("related_release") == rid])
    if ri: r["related_incidents"] = ri

# ---- write ----------------------------------------------------------------
def strip_none(o):
    if isinstance(o, dict):
        return {k: strip_none(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return [strip_none(x) for x in o]
    return o

def dump(path, obj):
    with open(os.path.join(H, path), "w") as f:
        json.dump(strip_none(obj), f, indent=2)
        f.write("\n")

dump("jira/jira_stories.json", stories)
dump("pull-requests/pull_requests.json", prs)
dump("commits/commits.json", commits)
dump("tests/test_cases.json", tests)
dump("incidents/incidents.json", incident_records)
dump("registry/releases.json", releases)

print(f"stories={len(stories)} prs={len(prs)} commits={len(commits)} "
      f"tests={len(tests)} incidents={len(incident_records)}")
print("PR commit counts sum =", sum(len(p['commits']) for p in prs))
