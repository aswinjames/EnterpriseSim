# Jev vs. GPT context-decision experiment (BC-0101)

**Status: completed.** Both providers have completed a 5-run live batch on this
case. For the results, comparison table, and findings, see
[`RESULTS.md`](RESULTS.md). This README covers the experiment's design and how to
reproduce or extend it; it does not duplicate the results themselves.

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
| `decision.py` | `ContextDecision` (one provider's per-candidate verdict) and `aggregate()` (seven decisions → one selected context set). |
| `providers/base.py` | `ContextDecisionProvider` ABC; the shared task statement and prompt-version tag both providers use. |
| `providers/openrouter.py` | Shared zero-dep `urllib` HTTP client (`post_json`), the two endpoint path constants, and the single `OPENROUTER_API_KEY` env var name. |
| `providers/mock_provider.py` | Deterministic offline decider for wiring tests / dry runs. **Not** a stand-in for Jev's or GPT's judgment. |
| `providers/gpt_provider.py` | Live GPT provider: pinned `openai/gpt-5-mini` via OpenRouter chat completions, structured JSON-schema output. |
| `providers/jev_provider.py` | Live Jev provider: pinned `typesafe/jev-1.13` via OpenRouter's alpha Decisions API, `noul`-type question. |
| `scoring.py` | Imports `score()` from `examples/quickstart/run_quickstart.py` unmodified — no invented `composition_quality` term. |
| `run_experiment.py` | CLI: runs N repeats for one provider, captures full per-repeat records, writes JSON to `results/` incrementally after every repeat (so a failure partway through a long live batch cannot erase already-completed repeats). |
| `tests/` | `unittest` coverage for all of the above, offline only — includes request-construction/response-parsing tests for both OpenRouter integrations with the network call itself mocked out. |

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
