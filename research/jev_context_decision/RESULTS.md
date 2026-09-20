# BC-0101 — Jev vs GPT Context Decision Experiment

## 1. Objective

This experiment tests how two different models make per-artifact context-inclusion
decisions for benchmark case [`BC-0101`](../../benchmarks/examples/benchmark_case.example.json)
(suite `BENCH-01`, Context Assembly), under identical conditions:

- **Jev 1.13** (`typesafe/jev-1.13`), TypeSafe's structured decision model, called via
  its native `noul` boolean-decision question type.
- **GPT-5 Mini** (`openai/gpt-5-mini`), called via structured JSON-schema output.
- **OpenRouter** as the single common gateway for both models.
- The same seven candidate artifacts, with their real content (not opaque IDs).
- The same task/trigger (`CHK-1421`).
- The same scoring function — the repo's own, unmodified `score()` from
  `examples/quickstart/run_quickstart.py`.

For each of the seven candidate artifacts, the experiment asks a single, independent
question: **should this artifact be included in the Worker's working context for this
task?** Each candidate is judged on its own; a provider never sees the other six
candidates or its own prior answers.

## 2. Experimental Setup

| Parameter | Value |
|---|---|
| Benchmark | `BC-0101` (suite `BENCH-01`) |
| Task / trigger | `CHK-1421` (guest checkout order placement, `APP-003`) |
| Candidate artifacts | 7 (`KN-045`, `KN-052`, `KN-063`, `KN-047`, `KN-101`, `EXP-090`, `EXP-055`) |
| Runs per provider | 5 independent runs |
| Candidate decisions per provider | 35 (7 candidates × 5 runs) |
| Total candidate decisions (both providers) | 70 |
| Candidate content | Identical across all runs and both providers — real content resolved from elsewhere in this repo (see `candidates.py`); `KN-047` has no body anywhere in the repo and is passed as an explicit content-unavailable stub |
| Prompt / task framing | Identical across all runs and both providers |
| Evaluator | The repo's own `score()` (`examples/quickstart/run_quickstart.py`), unmodified |
| Benchmark case / ground truth | Unmodified, read-only input |

**Exact model IDs used** (as returned by the API and recorded in the result files):

- Jev: `typesafe/jev-1.13-20260917`
- GPT: `openai/gpt-5-mini`

**Gateway:** OpenRouter (`https://openrouter.ai`) for both providers — Jev via the
alpha Decisions API (`/api/alpha/decisions`), GPT via standard chat completions
(`/api/v1/chat/completions`).

**Prompt/config version:** `jev-gpt-openrouter-context-decision-v2` (identical for
every run of both providers in this experiment).

## 3. Ground Truth

Exactly as it exists in `benchmarks/examples/benchmark_case.example.json`
(`ground_truth`), read-only and unmodified by this experiment:

```json
{
  "type": "reference_set",
  "must_include": ["KN-045", "KN-052", "EXP-090"],
  "must_exclude": ["KN-101"],
  "expected": {
    "code": ["mcg-checkout-service/src/checkout/PlaceOrder.java"],
    "acceptable_optional": ["KN-063", "EXP-055"]
  },
  "source": "CTX-0118",
  "notes": "KN-101 (marketplace seller onboarding) is an out-of-scope distractor; KN-047 (legacy monolith checkout) is a defensible budget drop but not required."
}
```

- **must_include:** `KN-045`, `KN-052`, `EXP-090`
- **must_exclude:** `KN-101`
- **acceptable_optional** (counted in recall/precision, but neither required nor forbidden): `KN-063`, `EXP-055`
- `KN-047` is called a "defensible budget drop" only in `ground_truth.notes` — it is **not** in `acceptable_optional`, so the scorer's "relevant" set (`must_include ∪ acceptable_optional`) excludes it either way.

## 4. Results

| Provider | Runs | Mean Score | Recall | Precision | Verdict | Mean Latency | Mean Input Tokens | Mean Output Tokens | Mean Cost | Mean Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| Jev (`typesafe/jev-1.13-20260917`) | 5 | 0.400 | 0.800 | 0.800 | fail (5/5) | 425,448 ms (~7 min 5 s) | 4425 | 154 | $0.0001859 | 0.856 |
| GPT (`openai/gpt-5-mini`) | 5 | 0.400 | 0.800 | 0.800 | fail (5/5) | 436,743 ms (~7 min 17 s) | 1769 | 717.2 | $0.0018767 | 0.799 |

All values above are computed directly from the raw result files (see §9); none are
invented or estimated. Score, recall, precision, and verdict had zero variance across
each provider's 5 runs (min = max = mean in every run).

Ranges for the metrics that did vary:

| Metric | Jev range | GPT range |
|---|---|---|
| Latency (total, ms) | [425,298, 425,673] | [434,643, 440,956] |
| Output tokens | [154, 154] | [670, 750] |
| Cost (USD) | [$0.0001859, $0.0001859] | [$0.0017823, $0.0019423] |
| Mean confidence (per run) | [0.853, 0.860] | [0.730, 0.854] |

## 5. Context Selection

**Both providers selected the identical artifact set in all 5 runs each:**

- **Included:** `EXP-090`, `KN-045`, `KN-052`, `KN-063`, `KN-101`
- **Excluded:** `KN-047`, `EXP-055`

The selected set did not vary between the five runs for either provider — every run,
for both providers, produced exactly this five-item included set and two-item
excluded set.

**`KN-101` specifically:** `KN-101` is the sole `must_exclude` item in the ground
truth. Both providers included it in every one of their 5 runs. Its real, resolvable
content in this repository (`enterprise/knowledge/business-rules.json`) is titled
"Regional price resolution and currency binding" and concerns how the Pricing
Service (`APP-007`) resolves a price per (SKU, region, currency, channel) — a topic
plausibly relevant to computing order totals during checkout. This differs from the
benchmark case's own `ground_truth.notes`, which describes `KN-101` as "marketplace
seller onboarding." Both providers' stated rationales (recorded verbatim in the raw
result files) reasoned about price/currency resolution being relevant to guest
checkout order totals — consistent with `KN-101`'s actual retrievable content, not
with the "marketplace seller onboarding" characterization in the ground truth notes.

## 6. Observed Findings

- Both providers selected the same artifact set in all five runs.
- Both providers included all three required artifacts (`KN-045`, `KN-052`, `EXP-090`) in every run.
- Both providers also selected `KN-101` in every run.
- Both therefore received the same benchmark score (0.400) and verdict (`fail`) in every run.
- Jev's measured API cost was lower than GPT-5 Mini's in this experiment (mean $0.0001859 vs. $0.0018767 per 7-candidate run).
- Latency was broadly similar between the two providers (mean ~425.4 s vs. ~436.7 s per 7-candidate run).
- Jev showed essentially no variation in its aggregate decisions across runs (per-candidate confidence values varied by at most 0.02 across the 5 runs).
- GPT showed stable final selections while its confidence and output-token counts varied between runs (per-candidate confidence ranged as widely as 0.21–0.95 for the same candidate across different runs; output tokens ranged 670–750).

## 7. Interpretation / Limitation

This experiment covers:

- one benchmark case (`BC-0101`),
- seven candidate artifacts,
- five repeated runs per provider,
- two specific model configurations (`typesafe/jev-1.13-20260917`, `openai/gpt-5-mini`), pinned to one prompt/config version.

This scope does not establish general superiority of either model, either at context
selection specifically or at any broader task. A single benchmark case with one
task/domain (guest checkout) and a small, fixed candidate set cannot be generalized
to other tasks, other candidate corpora, other model versions, or the EnterpriseSim
Worker architecture as a whole.

**Observed failure mode:** both models successfully identified all three required
artifacts in every run, but both also consistently admitted `KN-101`, which
`benchmark_case.example.json`'s ground truth marks as a forbidden distractor. As
noted in §5, `KN-101`'s actual retrievable content is about price/currency
resolution, not the "marketplace seller onboarding" topic the ground truth's notes
field describes — which is a plausible contributor to why both models, independently,
reasoned it relevant to computing checkout order totals. This is described here as an
observed context-selection outcome on this one benchmark case, under this one
candidate-content resolution; it is not evidence that the broader EnterpriseSim
Worker architecture, its Context Layer design, or the BENCH-01 scoring methodology is
flawed.

## 8. Reproducibility

**Offline tests** (no network, no API key):

```bash
python3 -m unittest discover -s research/jev_context_decision/tests -t .
```

**Live runs** (require an OpenRouter API key with sufficient credit — real network
calls and real cost; do not run these without deliberately intending to spend
API credits):

```bash
# Requires OPENROUTER_API_KEY to be set in your shell environment.
# (Never pass the key value inline in a shared/logged context.)

# Single-run sanity check per provider:
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider jev --repeats 1 --live
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider gpt --repeats 1 --live

# Full 5-run batch per provider (as performed for this report):
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider jev --repeats 5 --live
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider gpt --repeats 5 --live
```

Live execution requires the environment variable `OPENROUTER_API_KEY` to be set
(this document does not include its value). Omitting `--live` always refuses to run
`jev`/`gpt`, even if the key is set, so a live run only ever happens when explicitly
requested.

## 9. Raw Results

Full, unmodified raw results for the two 5-run batches referenced throughout this
report:

- Jev: [`results/jev_20260920T092555Z.json`](results/jev_20260920T092555Z.json)
- GPT: [`results/gpt_20260920T095107Z.json`](results/gpt_20260920T095107Z.json)

Each file contains, per run: the selected included/excluded sets, required-item
presence/absence, forbidden-item selection, recall, precision, score, verdict,
latency, token counts, cost, per-candidate confidence, and the complete raw
per-candidate decision record (verdict, rationale, confidence, model, timestamp,
and the raw API response payload) for all 7 candidates — 35 raw decisions per file,
70 total. Contents are not duplicated here; see the files directly.

Two earlier single-run sanity-check result files also exist in `results/` from
before this 5-run batch (`jev_20260920T075349Z.json`, `gpt_20260920T081638Z.json`);
they are not part of the 5×5 data reported above but are retained as-is.

## 10. Next Experiment (proposed, not performed)

A natural follow-up — proposed here only, not executed as part of this experiment —
would test whether reframing the per-candidate decision criterion from general
**relevance/inclusion** ("is this artifact relevant to the task?") toward explicit
**task-specific necessity** ("is this artifact necessary to correctly complete this
specific task, as opposed to merely topically related to it?") changes the `KN-101`
outcome. `KN-101`'s content is topically related to checkout (price/currency
resolution) without being necessary for the specific guest-checkout order-placement
task BC-0101 describes; a necessity-framed criterion might filter it out where a
relevance-framed one does not. This would require a new prompt/config version and a
new experiment run — no such change has been made to the current experiment, its
prompts, or its configuration.
