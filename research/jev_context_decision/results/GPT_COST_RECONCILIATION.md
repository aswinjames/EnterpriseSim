# GPT Cost Reconciliation

Real, reconciled costs for the three GPT (direct OpenAI API) experiment
phases whose result JSON files correctly record `cost_usd_total: None` —
the direct OpenAI Chat Completions API does not return a per-call cost field
the way OpenRouter's passthrough does (see `research/jev_context_decision/README.md`,
"Known open items / history"). This document reconstructs the real billed
cost for those phases from OpenAI's own usage/cost exports and reports it
here, separately, without altering any historical record.

**This reconciliation does not modify any existing result JSON file, any
benchmark code, or any historical score/decision/confidence value.** It is a
supplementary cross-reference only.

## Reconciled costs

| | BC-0102 GPT (validation + 5×5) | X-RICH-1 GPT (5×5) | X-RICH-2 GPT (5×5) |
|---|---|---|---|
| Requests | 42 | 75 | 75 |
| Input tokens | 10,908 | 19,315 | 165,790 |
| Cached input tokens | 0 | 0 | 117,376 |
| Output tokens | 4,497 | 7,561 | 8,738 |
| **Real cost** | **$0.011721** | **$0.019951** | **$0.032514** |
| Approx. per repeat/run | $0.00234 | $0.00399 | $0.00650 |

These are **reconciled real costs, not estimates** — see provenance below.

## Provenance

- **BC-0102** request count (42) matches exactly: 7 requests for the single
  validation call (the original 7-candidate BC-0101/BC-0102 pool) + 35
  requests for the 5×5 run (7 candidates × 5 repeats) = 42 total.
- **X-RICH-1** request count (75) matches exactly: 15 candidates × 5 repeats.
- **X-RICH-2** request count (75) matches exactly: 15 candidates × 5 repeats.
- Request counts and timestamps were matched directly against the
  corresponding experiment result files — the attribution is exact, not
  inferred from approximate time windows.
- **X-RICH-2's $0.032514** is the exact, fully-attributed daily GPT-5-mini
  cost total from the OpenAI cost export for that day; no other GPT-5-mini
  activity occurred on that day, so the entire daily total belongs to this
  run with no ambiguity.
- **BC-0102 and X-RICH-1** (which share a calendar day) were reconstructed
  from their actual per-hour token counts using GPT-5-mini's published rates
  of $0.25/M input tokens and $2/M output tokens.
- That reconstruction reproduces the real Sept 20 billed daily total
  ($0.031672) to 6 decimal places when the two phases' computed costs are
  summed ($0.011721 + $0.019951 = $0.031672) — this exact match is why these
  figures are labeled **reconciled real costs**, not estimates.

## Prompt caching effect (X-RICH-2)

X-RICH-2 generated 165,790 input tokens across its 75 requests — of which
**117,376 (≈71%) were cached input tokens**, billed at $0.03/M rather than
the $0.25/M uncached rate. This is expected: X-RICH-2's sole experimental
treatment is appending the identical, complete enterprise application
registry (`enterprise/registry/applications.json`) to every one of the 75
requests, and repeated identical prompt content is exactly what OpenAI's
prompt caching discounts.

**Do not read the 8.6× increase in raw input tokens (19,315 → 165,790) as an
8.6× increase in actual cost.** The real cost increase was **≈1.63×**
($0.019951 → $0.032514 total; $0.00399 → $0.00650 per repeat) for the same
75-request, 5×5 experimental shape — most of the added token volume was
cache-discounted, not billed at the full uncached rate.

## Interpretation

1. X-RICH-2 materially increased input-token volume because the complete
   enterprise registry was added to every candidate decision.
2. Prompt caching substantially reduced the marginal billing impact of
   repeatedly supplying the same registry.
3. Therefore, cost analysis of enterprise-context experiments should
   consider both raw context size and cacheability/reuse — raw token counts
   alone overstate the real cost impact when the added content is identical
   across calls.
4. Cost is now available for GPT X-RICH-1 and X-RICH-2 through this
   reconciliation, even though the original result JSONs correctly retain
   `cost_usd_total: None` (an accurate record of what the API itself
   returned at the time, not an error).
5. This reconciliation does not alter benchmark scores, decisions,
   confidence values, or historical result files in any way.
