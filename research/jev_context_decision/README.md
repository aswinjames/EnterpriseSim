# Jev vs. GPT context-decision experiment (BC-0101 and onward)

**Status: this directory now spans five completed live experiments** —
BC-0101, BC-0102, X-RICH-1, X-RICH-2, and X-RICH-3 — run in that order as the
research question sharpened. **For the full narrative (why each experiment
exists, what changed between them, and what the evidence actually shows),
start with [`RESEARCH_STATE.md`](RESEARCH_STATE.md).** This README covers only
BC-0101's design and how to reproduce it; it predates BC-0102 and the X-RICH
series and was not rewritten to describe them (see below for where each one is
actually documented).

For BC-0101 itself: both providers completed a 5-run live batch. For the
results, comparison table, and findings, see [`RESULTS.md`](RESULTS.md).

**BC-0102** reframes BC-0101's criterion from general relevance to
task-specific necessity, on the same 7 candidates. Criterion: `providers/base.py::BC_0102`.
Results: `results/gpt_bc0102_directopenai_20260920T154844Z.json` (GPT, 5/5),
`results/jev_bc0102_20260920T111242Z.json` (Jev, 5/5). No standalone results
doc exists for BC-0102 beyond `RESEARCH_STATE.md`'s summary — read the JSON
files directly for full per-run detail.

**X-RICH-1** — a richer, 15-candidate follow-up (same BC-0101 criterion,
KN-101 now CONTESTED rather than a fixed `must_exclude`) — **has been run
live, 5×5, for both providers.** See
[`../EXPERIMENT_3_PROPOSAL.md`](../EXPERIMENT_3_PROPOSAL.md) for the design
rationale (written before execution; see its status note for where results
now live), `experiment_3_candidates.py` / `run_experiment_3.py` for the code,
and `tests/test_experiment_3_candidates.py` for its offline test coverage.
Results: `results/experiment3_jev_20260920T192733Z.json`,
`results/experiment3_gpt_20260920T194326Z.json`.

**X-RICH-2** adds the complete, unfiltered `enterprise/registry/applications.json`
to every X-RICH-1 candidate decision, testing whether explicit
application-dependency context changes selection (H1). Code:
`enterprise_context.py`, `providers/enterprise_context_providers.py`,
`run_experiment_x_rich_2.py`. Results: `results/xrich2_jev_20260921T015516Z.json`,
`results/xrich2_gpt_20260921T015607Z.json`. GPT cost impact of the added
registry: [`results/GPT_COST_RECONCILIATION.md`](results/GPT_COST_RECONCILIATION.md).

**X-RICH-3** adds a hard cap of 5 selected candidates on top of X-RICH-1
(pure post-hoc confidence-ranking over unchanged per-candidate decisions —
no new prompt). Code: `run_experiment_x_rich_3.py`. Results:
`results/xrich3_jev_20260921T031504Z.json` (5/5),
`results/xrich3_gpt_20260921T031529Z.json` (5/5).

BC-0101 and BC-0102 are unaffected by any of the X-RICH experiments — each is
implemented in separate, additive files that never modify the frozen
candidates, criteria, or historical result files described in the rest of
this README.

Compares two ways of making the BENCH-01 context-assembly decision for
[`BC-0101`](../../benchmarks/examples/benchmark_case.example.json) (guest checkout,
`CHK-1421`): Jev's native TypeSafe `noul` decision type vs. an equivalent
structured INCLUDE/EXCLUDE call to GPT. Each of the case's seven candidate
artifacts is judged **independently** ("should this one item be in the Worker's
working context?"), using its **real content** (not an opaque `KN-###`/`EXP-###`
ID) resolved live from elsewhere in this repo. The seven decisions are aggregated
into a selected context set and scored with the repo's own, unmodified `score()`
evaluator.

## Gateway: OpenRouter, for both providers

Both Jev and GPT are called through **OpenRouter** as the one gateway, each
pinned to a specific model:

| Provider | Pinned model | OpenRouter endpoint | Env var |
|---|---|---|---|
| Jev | `typesafe/jev-1.13` | `POST https://openrouter.ai/api/alpha/decisions` (the alpha Decisions API — deliberately outside the `/api/v1` prefix) | `OPENROUTER_API_KEY` |
| GPT | `openai/gpt-5-mini` | `POST https://openrouter.ai/api/v1/chat/completions` (standard OpenAI-compatible chat completions) | `OPENROUTER_API_KEY` |

Both env-var names are literally the same one (`OPENROUTER_API_KEY`) — there is a
single gateway key for both providers, not one key per model.

**This table describes BC-0101 only.** Starting with BC-0102, `GPTProvider`
moved to the direct OpenAI API (`OPENAI_API_KEY`, `providers/openai_direct.py`)
after repeated OpenRouter credit/truncation failures — see "Known open items /
history" below. `JevProvider` has used OpenRouter for every experiment in this
directory, including X-RICH-1/2/3. So as of BC-0102 onward: Jev via
OpenRouter, GPT via direct OpenAI — two different gateways, two different env
vars, not one shared gateway.

Both pinned slugs above are what's requested; the API echoes back a more specific,
dated model identifier actually served, recorded per-decision in the result files.
For the completed 5×5 batch (see `RESULTS.md`) that was `typesafe/jev-1.13-20260917`
and `openai/gpt-5-mini`.

There is **no** dependency on the OpenAI SDK or on any native `noul` client
library — both providers make plain HTTPS calls with `urllib` (stdlib only), via
the shared `providers/openrouter.py` helper. This replaces the earlier iteration
of this experiment, which used the direct OpenAI SDK for GPT and an unverified
native `noul` client for Jev.

### Jev / `noul` on OpenRouter

`typesafe/jev-1.13` is TypeSafe's "System One" decision model: instead of
generating text, it takes an app's state plus a typed question and returns a
typed decision with a probability attached. OpenRouter's Decisions API exposes a
`"type": "noul"` question — a boolean decision type that returns a bare
probability (e.g. `{"type": "noul", "noul": 0.93}`) — which is exactly the
"typed choice with an attached probability" semantics `noul` was always meant to
express. `providers/jev_provider.py` asks exactly one `noul` question per
candidate ("should this be included?") and maps the returned probability to
`include`/`exclude` at a 0.5 threshold, with `confidence` = the probability of
whichever verdict was chosen.

Sources (fetched live while implementing this):
- https://openrouter.ai/typesafe/jev-1.13
- https://openrouter.ai/docs/cookbook/evaluate-and-optimize/jev-verified-cascade (states the Decisions API path explicitly, outside `/api/v1`)
- https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request (request/response schema, including the `noul` question type and example payloads)

### GPT on OpenRouter

`openai/gpt-5-mini` is called via the standard chat-completions endpoint with
`response_format: {"type": "json_schema", ...}` (strict mode), returning
`{"verdict", "rationale", "confidence"}` — unchanged in shape from the
pre-OpenRouter version, only the transport and pinned model changed.

## Layout

| File | Purpose |
|---|---|
| `candidates.py` | Resolves the seven BC-0101 candidate IDs to real content already on disk (`enterprise/knowledge/*.json`, `schemas/examples/knowledge_object.example.json`, `corpus/experience_store.json`). `KN-047` has no body anywhere in the repo — every reference to it is provenance-only — so it resolves to an explicit `CONTENT_UNAVAILABLE` stub rather than invented text. |
| `task_scope.py` | `TaskScope` — explicit, structured representation of what a task declares (id, title, description, declared apps, code target); see [Task Scope](#task-scope) below. |
| `benchmark_quality.py` | Documents the known KN-101 ground-truth/content discrepancy as a testable record, without altering either side; see [Benchmark-quality finding](#benchmark-quality-finding-kn-101) below. |
| `decision.py` | `ContextDecision` (one provider's per-candidate verdict) and `aggregate()` (seven decisions → one selected context set). |
| `providers/base.py` | `ContextDecisionProvider` ABC and `DecisionCase` (criterion wording + prompt version + `task_scope`) shared by BC-0101/BC-0102. |
| `providers/openrouter.py` | Shared zero-dep `urllib` HTTP client (`post_json`) used by `JevProvider`; the alpha Decisions path and the `OPENROUTER_API_KEY` env var name. |
| `providers/openai_direct.py` | Shared zero-dep `urllib` HTTP client used by `GPTProvider` to call OpenAI directly (not OpenRouter); the `OPENAI_API_KEY` env var name. |
| `providers/mock_provider.py` | Deterministic offline decider for wiring tests / dry runs. **Not** a stand-in for Jev's or GPT's judgment. |
| `providers/gpt_provider.py` | Live GPT provider: pinned `gpt-5-mini` via the direct OpenAI chat-completions API, structured JSON-schema output. |
| `providers/jev_provider.py` | Live Jev provider: pinned `typesafe/jev-1.13` via OpenRouter's alpha Decisions API, `noul`-type question. |
| `scoring.py` | Imports `score()` from `examples/quickstart/run_quickstart.py` unmodified — no invented `composition_quality` term. |
| `run_experiment.py` | CLI: runs N repeats for one provider under a chosen `--criterion` (`bc-0101`/`bc-0102`), captures full per-repeat records, writes JSON to `results/` incrementally after every repeat (so a failure partway through a long live batch cannot erase already-completed repeats). |
| `tests/` | `unittest` coverage for all of the above, offline only — includes request-construction/response-parsing tests for both provider transports with the network call itself mocked out. |

## Ground truth, exactly as it exists in `benchmark_case.example.json`

- `must_include`: `KN-045`, `KN-052`, `EXP-090`
- `must_exclude`: `KN-101`
- `acceptable_optional` (counted in recall/precision, but neither required nor forbidden): `KN-063`, `EXP-055`
- `KN-047` is called a "defensible budget drop" in `ground_truth.notes` only — it is **not** in `acceptable_optional`, so it is not part of the "relevant" set the scorer computes recall/precision against either way.

Nothing in this directory modifies the benchmark case or its ground truth; both are read-only inputs.

## Running

```bash
# Offline wiring check — no network, no API key:
python3 -m research.jev_context_decision.run_experiment --provider mock --repeats 1

# Tests:
python3 -m unittest discover -s research/jev_context_decision/tests -t .
```

Live runs require **both** `--live` and `OPENROUTER_API_KEY` — omitting `--live`
always refuses, even if the key is set, so this tool cannot make an accidental
paid call:

```bash
# First live Jev sanity test:
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider jev --repeats 1 --live

# First live GPT sanity test:
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider gpt --repeats 1 --live

# Full x5 runs, once sanity tests pass (this is what produced the results in RESULTS.md):
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider jev --repeats 5 --live
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider gpt --repeats 5 --live
```

The commands above are exactly what produced BC-0101's `RESULTS.md` data and
still work unchanged for BC-0101. For **BC-0102** (`--criterion bc-0102`) and
every X-RICH experiment, `gpt` requires `OPENAI_API_KEY` instead (direct
OpenAI API, not OpenRouter) — see the gateway note above and each
experiment's own runner (`run_experiment.py --help`, `run_experiment_3.py`,
`run_experiment_x_rich_2.py`, `run_experiment_x_rich_3.py`) for its exact
invocation.

Each 7-candidate repeat takes roughly 60s per candidate (sequential, ~7 minutes per
repeat), so a 5-repeat batch takes on the order of 35 minutes per provider.

## Raw results

The completed 5×5 batch that `RESULTS.md` reports on:

- Jev: [`results/jev_20260920T092555Z.json`](results/jev_20260920T092555Z.json)
- GPT: [`results/gpt_20260920T095107Z.json`](results/gpt_20260920T095107Z.json)

Two earlier single-run sanity-check files also remain in `results/`
(`jev_20260920T075349Z.json`, `gpt_20260920T081638Z.json`) from before the 5-run
batch; they predate the fixes below and are not part of the reported 5×5 data.

## Known open items / history

- The Decisions API is documented as **alpha** by OpenRouter; its request/response shape (in particular the `noul` question type) may change without notice. `providers/jev_provider.py::_parse_response` reads `response["answers"][key]["noul"]` directly — if OpenRouter changes this shape, a live Jev call will surface it as a `KeyError`, not a silent misparse. This did not occur during the completed 5×5 batch.
- Pricing/latency for both pinned models were current as of the OpenRouter pages fetched while implementing this; re-check `openrouter.ai/typesafe/jev-1.13` and `openrouter.ai/openai/gpt-5-mini` before running further live batches at scale if cost matters.
- `openai/gpt-5-mini` is a reasoning model: hidden reasoning tokens draw from the same `max_tokens` budget as the visible JSON answer, and reasoning-token spend varies per call. Two live truncation failures (`finish_reason=length`, an `Unterminated string` JSON parse error) were observed while first exercising the GPT provider before the reported 5×5 batch. Fixed by setting `reasoning: {"effort": "minimal"}` and raising `gpt_provider.MAX_OUTPUT_TOKENS` to 4000 (a safety margin only — no change to the prompt, schema, or model pin), plus a clear `RuntimeError` on `finish_reason == "length"` instead of an opaque JSON parse error. The reported 5×5 GPT batch completed cleanly under this fixed configuration.
- `GPTProvider` later moved from OpenRouter to the direct OpenAI API (`providers/openai_direct.py`, `OPENAI_API_KEY`) to complete the BC-0102 GPT batch after repeated OpenRouter credit/truncation failures. `JevProvider` is unaffected and still uses OpenRouter (`OPENROUTER_API_KEY`). This changed only transport and two OpenAI-specific parameter names (`max_tokens`→`max_completion_tokens`, `reasoning.effort`→`reasoning_effort`, same values) — not the prompt, schema, or model.

## Task Scope

**What it is.** `task_scope.py::TaskScope` is an explicit, structured representation of
what a task declares about itself: `task_id`, `title`, `description`, `declared_apps`,
`code_target`, and `trigger_type`. It is one of five concepts this codebase keeps
deliberately separate:

1. **Artifact content** — what a candidate actually says (`candidates.py`)
2. **Artifact metadata** — app/type/id/title/relationships (`Candidate.raw`)
3. **Task scope** — what the task explicitly declares (`task_scope.py`, this section)
4. **Decision criterion** — why to include/exclude an artifact (`providers/base.py::DecisionCase`)
5. **Ground truth** — the benchmark's expected answer (`benchmark_case["ground_truth"]`)

**Why add it.** BC-0101/BC-0102 showed that a context decision can depend on whether a
model understands what application is being worked on, what code path is being changed,
what other applications are explicitly in scope, and what the task is actually trying to
accomplish. Today, a provider only sees candidate title/body text and the criterion
question — it has no structured signal about the task's own declared boundaries. Making
task scope an explicit, reusable object is a prerequisite for testing whether that signal
would help, without redesigning anything else.

**What it is not, and does not do.** `TaskScope` carries zero candidate-specific
information and zero decision logic. It does not know `KN-101` or `KN-063` exist, and it
does not encode a rule like "exclude every artifact from an app not in `declared_apps`" —
such a rule would be wrong: `KN-063` belongs to `APP-008` (not a declared app) but is
`acceptable_optional`, precisely because it explicitly references the declared task despite
its own app being out of scope. `TaskScope` is pure data; `tests/test_task_scope.py`
verifies structurally that the class has no method capable of producing an include/exclude
verdict for anything.

**Where it lives today.** `providers/base.py::DecisionCase` now carries a `task_scope`
field, derived once from the frozen benchmark case and attached identically to both
`BC_0101` and `BC_0102` (same underlying task, same scope, only the criterion wording
differs). **It is not threaded into any live prompt** — `gpt_provider.py`/`jev_provider.py`
build their requests from `task_statement`/`jev_instructions`/`jev_criteria_*` exactly as
before; adding `task_scope` changes nothing about what was previously sent over the wire
for either historical case (`tests/test_task_scope.py::TestTaskScopeNeverThreadedIntoLivePrompts`
verifies this directly). It exists so a *future*, separately-versioned criterion could
choose to have its provider reference `case.task_scope` when building a prompt, without
any change to the `decide(candidate, case=...)` interface.

## Benchmark-quality finding: KN-101

`benchmark_quality.py::KN_101_DISCREPANCY` documents a real inconsistency, found while
reviewing BC-0101/BC-0102 results, between two descriptions of the same candidate:

| | Says |
|---|---|
| `benchmarks/examples/benchmark_case.example.json`'s `ground_truth.notes` | "marketplace seller onboarding" |
| `KN-101`'s actual, resolvable content (`enterprise/knowledge/business-rules.json`, via `candidates.py`) | "Regional price resolution and currency binding" |

These describe different subjects. This is **documented, not corrected** — BC-0101 and
BC-0102 are frozen historical experiments, and neither the ground-truth note nor KN-101's
content has been changed to make them agree. `tests/test_benchmark_quality.py` asserts the
discrepancy still holds today, so any future edit to either side becomes a visible,
deliberate decision rather than silent drift.

**Why this matters for benchmark validity:** both Jev and GPT, reasoning from KN-101's real
content, gave plausible rationales for including it (price/currency resolution is
relevant to computing an order total). Neither model could have reconstructed
"marketplace seller onboarding" as a reason to exclude it, because nothing they were shown
says that. Any interpretation of *why* KN-101 is `must_exclude` that leans on the
ground-truth note's framing is not verifiable against what a Worker actually sees — the
note and the content it's attached to are, on this evidence, about two different things.

## Future experiment direction (documented, not implemented)

A natural follow-up — proposed here only, not built or run — is to compare:

**A.** artifact content only (the current setup)

against

**B.** artifact content **+** explicit task scope (handing `case.task_scope` to the
provider when building its prompt)

while holding constant: candidate set, criterion wording, ground truth, scoring, model,
provider, and every other prompt element. This would test whether explicit structured
task-scope information changes context-selection behavior, independent of a change in the
decision criterion (which is what BC-0101→BC-0102 already tested). This is not named
`BC-0103` — there is no established case-numbering mechanism in this codebase requiring
that, and no such case has been created, run, or scored.
