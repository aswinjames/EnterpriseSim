#!/usr/bin/env python3
"""Generate Part 3 — six months of engineering history.

Synthesizes per-sprint evolution digests (13) and release notes (10) purely from the
already-generated, validated reference artifacts, so every line references a real ID.
Each sprint digest covers: new features, technical debt, architecture changes, new APIs,
business-rule changes, incidents, hotfixes, release notes, knowledge updates, experience
updates and evaluation improvements. Also emits evolution/timeline.json.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timedelta
from statistics import mean

H = os.path.expanduser("~/EnterpriseSim")
L = lambda p: json.load(open(f"{H}/{p}"))
apps = {a["id"]: a for a in L("enterprise/registry/applications.json")}
stories = L("enterprise/jira/jira_stories.json")
prs = {p["id"]: p for p in L("enterprise/pull-requests/pull_requests.json")}
incidents = L("enterprise/incidents/incidents.json")
releases = {r["sprint"]: r for r in L("enterprise/registry/releases.json")}
km = {o["id"]: o for o in L("enterprise/knowledge/index.json")}
corpus = L("corpus/index.json")
experiences = {e["id"]: e for e in L("corpus/experience_store.json")}

def sprint_of(dtstr):
    d = datetime.strptime(dtstr[:10], "%Y-%m-%d")
    return max(1, min(13, ((d - datetime(2026, 1, 5)).days // 14) + 1))

def win(s):
    a = datetime(2026, 1, 5) + timedelta(days=(s - 1) * 14)
    return a.strftime("%Y-%m-%d"), (a + timedelta(days=11)).strftime("%Y-%m-%d")

# index artifacts by sprint
inc_by_sprint = {}
for i in incidents:
    inc_by_sprint.setdefault(sprint_of(i["detected_at"]), []).append(i)
runs_by_sprint = {}
for r in corpus:
    runs_by_sprint.setdefault(r["sprint"], []).append(r)
stories_by_sprint = {}
for s in stories:
    stories_by_sprint.setdefault(s["sprint"], []).append(s)

# business-rule / arch / api knowledge by app for "changes" attribution
def kn_for_apps(appset, doc_type, limit=4):
    out = []
    for kid, o in km.items():
        if o.get("metadata", {}).get("doc_type") == doc_type and o.get("app") in appset:
            out.append(kid)
    return sorted(out)[:limit]

def bullet(items):
    return "\n".join(f"- {x}" for x in items) if items else "- _(none this sprint)_"

timeline = []
prev_eval = None
for s in range(1, 14):
    start, end = win(s)
    sstories = stories_by_sprint.get(s, [])
    feats = [st for st in sstories if st["type"] == "story"]
    debt = [st for st in sstories if st["type"] in ("task", "spike") or "tech-debt" in st.get("labels", [])]
    bugs = [st for st in sstories if st["type"] == "bug"]
    sincs = inc_by_sprint.get(s, [])
    hotfix_prs = [p for p in prs.values() if p.get("is_hotfix") and sprint_of(p["created_at"]) == s]
    sruns = runs_by_sprint.get(s, [])
    rel = releases.get(s)
    appset = set()
    for st in sstories: appset.add(st["app"])
    if rel: appset |= set(rel["apps"])
    # knowledge updates: postmortems for this sprint's incidents + promoted experiences
    pm_updates = [i.get("postmortem") for i in sincs if i.get("postmortem")]
    exp_updates = sorted({r["experience"] for r in sruns})
    created = [r["experience"] for r in sruns if r["experience_update"] == "created"]
    # evaluation improvement
    eval_now = round(mean([r["score"] for r in sruns]), 3) if sruns else None
    conf_now = round(mean([r["fused_confidence"] for r in sruns]), 3) if sruns else None
    delta = None
    if eval_now is not None and prev_eval is not None:
        delta = round(eval_now - prev_eval, 3)

    lines = []
    lines.append(f"# Sprint {s} — Engineering Evolution ({start} → {end})")
    lines.append("")
    lines.append(f"> Part of [six months of MCG engineering history](../README.md). "
                 f"{'Release train **' + rel['id'] + ' — ' + rel['name'] + '**.' if rel else 'No release train this sprint (continued evolution).'}")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Stories delivered | {len(sstories)} ({len(feats)} features, {len(debt)} debt/spikes, {len(bugs)} bugs) |")
    lines.append(f"| Incidents | {len(sincs)} |")
    lines.append(f"| Hotfixes | {len(hotfix_prs)} |")
    lines.append(f"| Worker executions (corpus) | {len(sruns)} |")
    if eval_now is not None:
        lines.append(f"| Mean evaluation score | {eval_now}{'  (Δ ' + ('+' if delta>=0 else '') + str(delta) + ')' if delta is not None else ''} |")
        lines.append(f"| Mean fused confidence | {conf_now} |")
    lines.append("")

    lines.append("## New features")
    lines.append(bullet([f"`{st['id']}` {st['title']} ({st['app']})" for st in feats[:10]]))
    lines.append("")
    lines.append("## Technical debt")
    lines.append(bullet([f"`{st['id']}` {st['title']} ({st['app']})" for st in debt[:8]]))
    lines.append("")
    lines.append("## Architecture changes")
    ad = kn_for_apps(appset, "architecture", 4)
    lines.append(bullet([f"`{k}` {km[k]['title']}" for k in ad]))
    lines.append("")
    lines.append("## New / updated APIs")
    api = kn_for_apps(appset, "api_spec", 4)
    lines.append(bullet([f"`{k}` {km[k]['title']}" for k in api]))
    lines.append("")
    lines.append("## Business-rule changes")
    br = [k for k, o in km.items() if o.get("metadata", {}).get("doc_type") == "business_rule" and o.get("app") in appset][:5]
    lines.append(bullet([f"`{k}` {km[k]['title']}" for k in sorted(br)]))
    lines.append("")
    lines.append("## Incidents")
    lines.append(bullet([f"`{i['id']}` [{i['severity']}] {i['title']} — root cause: {i['root_cause_category']}"
                         + (f" → hotfix `{i['hotfix_pr']}`" if i.get("hotfix_pr") else "") for i in sincs]))
    lines.append("")
    lines.append("## Hotfixes")
    lines.append(bullet([f"`{p['id']}` {p['title']}" for p in hotfix_prs]))
    lines.append("")
    lines.append("## Release notes")
    if rel:
        lines.append(f"See [`{rel['id']}`](../release-notes/{rel['id']}.md) — {rel['theme']}")
    else:
        lines.append("- _(no release train; changes rolled continuously)_")
    lines.append("")
    lines.append("## Knowledge updates")
    ku = [f"`{k}` postmortem ({km[k]['title']})" for k in pm_updates if k in km]
    lines.append(bullet(ku))
    lines.append("")
    lines.append("## Experience updates")
    eu = []
    for e in exp_updates:
        obj = experiences.get(e)
        tag = "created" if e in created else "reinforced"
        eu.append(f"`{e}` {tag} — {obj['lesson'][:80] if obj else ''}")
    lines.append(bullet(eu))
    lines.append("")
    lines.append("## Evaluation improvements")
    if eval_now is not None:
        trend = "first measured sprint" if delta is None else (f"up {delta:+.3f} vs previous sprint" if delta >= 0 else f"down {delta:+.3f} vs previous sprint")
        lines.append(f"- Mean Worker evaluation score **{eval_now}** ({trend}); mean fused confidence **{conf_now}**.")
        lines.append(f"- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).")
    else:
        lines.append("- _(no corpus executions recorded this sprint)_")
    lines.append("")

    open(f"{H}/evolution/sprints/SPRINT-{s:02d}.md", "w").write("\n".join(lines) + "\n")
    timeline.append({"sprint": s, "window": [start, end], "release": rel["id"] if rel else None,
                     "stories": len(sstories), "features": len(feats), "debt": len(debt), "bugs": len(bugs),
                     "incidents": [i["id"] for i in sincs], "hotfixes": [p["id"] for p in hotfix_prs],
                     "executions": len(sruns), "mean_eval_score": eval_now, "mean_fused_confidence": conf_now,
                     "experiences_created": created, "experiences_reinforced": [e for e in exp_updates if e not in created]})
    if eval_now is not None:
        prev_eval = eval_now

# release notes
for s, rel in sorted(releases.items()):
    start, end = win(s)
    sincs = inc_by_sprint.get(s, [])
    L2 = []
    L2.append(f"# Release Notes — {rel['id']}: {rel['name']}")
    L2.append("")
    L2.append(f"- **Date:** {rel['date'][:10]}  •  **Sprint:** {rel['sprint']}  •  **Status:** {rel['status']}")
    L2.append(f"- **Applications:** {', '.join(rel['apps'])}")
    L2.append("")
    L2.append(f"## Theme\n\n{rel['theme']}")
    L2.append("")
    L2.append("## Highlights")
    L2.append(bullet(rel.get("highlights", [])))
    L2.append("")
    L2.append("## Included stories")
    L2.append(bullet([f"`{sid}`" for sid in rel.get("included_stories", [])]))
    L2.append("")
    L2.append("## Included pull requests")
    L2.append(bullet([f"`{pid}` {prs[pid]['title']}" if pid in prs else f"`{pid}`" for pid in rel.get("included_prs", [])]))
    L2.append("")
    if rel.get("related_incidents"):
        L2.append("## Related incidents")
        L2.append(bullet([f"`{iid}`" for iid in rel["related_incidents"]]))
        L2.append("")
    L2.append("## Rollback")
    L2.append("Per CANON-001 §7.4: progressive delivery with automated rollback on SLO breach; "
              "backward-compatible (expand-contract) migrations so rollback never requires a schema down-migration.")
    L2.append("")
    open(f"{H}/evolution/release-notes/{rel['id']}.md", "w").write("\n".join(L2) + "\n")

json.dump(timeline, open(f"{H}/evolution/timeline.json", "w"), indent=2)
open(f"{H}/evolution/timeline.json", "a").write("\n")

scores = [t["mean_eval_score"] for t in timeline if t["mean_eval_score"]]
print(f"sprints={len([1 for _ in range(13)])} release_notes={len(releases)}")
print(f"eval score trend: sprint1={scores[0]} -> sprint13={scores[-1]}  (min {min(scores)}, max {max(scores)})")
