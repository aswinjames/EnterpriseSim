# EnterpriseSim Research: What Should an AI Worker Remember?

**What this document is.** This is the canonical write-up of the context-assembly
research in `research/jev_context_decision/` — why I built it, what I tested,
what happened, and what I still don't know. Every number below is read
directly from a result file, a reconciled cost document, or test output
already in this repository; nothing here is estimated or invented. For full
per-run detail, the underlying JSON files are in `results/`.

## Why I built EnterpriseSim

EnterpriseSim exists to simulate enterprise situations and see how an AI
Worker actually behaves inside them. This is the first of a set of use cases
I intend to build out and publish — the checkout scenario below is one
concrete exercise, not a claim that I've modeled an entire real enterprise.

What I wanted was a controlled environment where I could define a scenario,
define the candidate information or actions available to an agent, ask it to
make a decision, repeat that decision, inspect exactly what happened, and
score it. That loop — define, decide, repeat, inspect, evaluate — is the
whole point of the project. It's open-source, it's a testbed, and it doesn't
solve context assembly by existing. It just gives me somewhere to ask the
question and get an actual answer back instead of an opinion.

## The problem I was actually trying to test

An AI Worker doing real enterprise work can potentially reach a huge amount
of internal knowledge — checkout rules, payment rules, loyalty behavior,
pricing policy, past incidents, application dependencies, operational
runbooks. The question I kept running into, phrased a dozen different ways by
different people, was: how does the Worker decide what actually deserves a
place in its working context for one specific task?

My first instinct was to treat this as a retrieval problem — find the
relevant stuff, rank it, done. But once a system can technically retrieve
almost anything connected to a task, retrieval isn't the bottleneck anymore.
Deciding what to keep is. Context assembly isn't retrieval. It's a selection
and prioritization problem.

Take a concrete case: a Worker is responsible for placing a guest checkout
order. It has access to checkout domain rules, an idempotency standard, a
rule about loyalty accounts, pricing/promo policy, past incident writeups,
application dependency data, and a pile of other enterprise documentation.
It can't carry all of it into every decision. Some of that material is
essential, some is useful but optional, some is genuinely related to
checkout but not necessary for this task, some is irrelevant, some doesn't
even resolve to real content, and — as I found out — at least one artifact
is just genuinely ambiguous. So the question becomes: how do I measure
whether the Worker is making the right call, artifact by artifact?

## Why I started experimenting with Jev

A lot of agent evaluation eventually comes down to judging a decision, not
generating a final answer: should this artifact be included, is this
information necessary, which tool should the agent use, should it take this
action, what should it keep when it can't keep everything. That's a
different kind of question than "write me the answer," and I wanted to know
whether a structured, decision-oriented model would be useful for evaluating
that kind of agent behavior — as opposed to using a general-purpose model and
parsing free text out of it.

That's the actual reason Jev (`typesafe/jev-1.13`) shows up throughout this
research, next to GPT (`openai/gpt-5-mini`). I'm not claiming Jev is a better
model, a better judge, or that its decisions are ready to use as training
labels — none of that is established here. What I can say, and what the
experiments below actually support, is narrower: Jev gave me a structured
decision interface that was fast and cheap enough to make repeated
experimentation practical, and a second, independently-built reasoning path
to compare against GPT's.

## Turning it into an experiment

EnterpriseSim gives me the substrate for this: real interconnected knowledge
base entries, incident writeups, experience records, and an
application-dependency registry (`enterprise/registry/applications.json`),
plus a benchmark harness (`score()`) that grades a selected context set
against a fixed ground truth. The loop is:

```
Task
  ↓
Candidate enterprise artifacts
  ↓
Context-selection decisions (include / exclude, per candidate)
  ↓
Working context (the selected set)
  ↓
Evaluation (recall, precision, required-item gate, objective score)
```

The task under study throughout is `CHK-1421`: guest checkout order
placement, on the Checkout Service (`APP-003`). Everything below is the same
task, run through five experiments that each changed exactly one thing.

| Experiment | Candidates | Criterion | What changed | Status |
|---|---|---|---|---|
| BC-0101 | 7 | Relevance ("should this be included?") | Baseline | Complete, 5×5 |
| BC-0102 | Same 7 | Necessity ("is this necessary to correctly perform this task?") | Criterion wording only | Complete, 5×5 |
| X-RICH-1 | 15 (7 + 8 new) | BC-0101's criterion, reused unchanged | Candidate pool enriched; `KN-101` reclassified CONTESTED | Complete, 5×5 |
| X-RICH-2 | Same 15 | Same as X-RICH-1 | Complete, unfiltered application-dependency registry added to every prompt | Complete, 5×5 |
| X-RICH-3 | Same 15 | Same as X-RICH-1 | Hard cap of 5 selected candidates, enforced mechanically after the fact | Complete, 5×5 |

Both models, throughout: Jev via OpenRouter's alpha Decisions API; GPT via
OpenRouter for `BC-0101`, then via the direct OpenAI API from `BC-0102`
onward (OpenRouter kept truncating GPT's responses and burning credit before
a batch finished — that's the whole reason for the switch, and it means
`BC-0101`'s GPT cost/latency numbers aren't directly comparable to anything
after it).

## Experiment 1 — Is relevance enough? (`BC-0101`)

Seven candidates, one question per candidate, asked independently: "should
this be included in the Worker's working context for this task?" Five runs
each.

Both models picked the exact same 5-item set every run and scored 0.400 —
a fail. Both included one artifact, every single run, that the ground truth
said should be excluded: `KN-101`, described in the benchmark's own notes as
"marketplace seller onboarding," an out-of-scope distractor.

I went and read what `KN-101` actually says. It isn't about marketplace
seller onboarding at all — it's about regional price resolution and currency
binding, how a pricing service resolves a price per SKU/region/currency/
channel. The application registry confirms Checkout has a real, declared
dependency on the Pricing service, the app that owns `KN-101`.

That changes the story. Both models weren't missing an obvious distractor —
they were reading real content about a real dependency and reasoning it
might matter for computing an order total. Neither could have reconstructed
"marketplace seller onboarding" as a reason to exclude it, because nothing
they were shown said that.

This is a benchmark-quality finding, not a resolved one. I'm not concluding
`KN-101` should be included, and I'm not concluding it should be excluded
either. I left the original ground-truth label untouched — it's a frozen,
historical result. But I stopped trusting that artifact as an unambiguous
distractor, and every experiment after this one treats it differently. The
lesson that stuck with me: the benchmark itself needed auditing against the
artifacts it claims to evaluate, not just the model behavior against the
benchmark.

## Experiment 2 — What does "necessary" mean? (`BC-0102`)

Same 7 candidates. I changed only the question, from relevance to
task-specific necessity: *"Is this artifact necessary to correctly perform
this specific task? Include it only if omitting it would materially reduce
the Worker's ability to complete the task correctly."* Something can be
related to checkout without being necessary to place an order correctly —
`KN-101` being the obvious thing to test that distinction against.

With the necessity framing: GPT still selected `KN-101` in 5 of 5 runs —
identical to `BC-0101` — and every run failed the gate because of it (mean
score 0.3868). Jev's rate dropped from an effective 5/5 to 2 of 5 runs (mean
score 0.5848, a mix of partial and fail). Reframing the question changed the
outcome for one model and, in any meaningful way, not for the other. I can't
say why from this data alone — I changed one variable and got two different
responses from two different models, which at minimum tells me the wording
distinction is real enough to matter and isn't something either model was
already applying by default.

## Experiment 3 — A richer enterprise (`X-RICH-1`)

The 7-candidate pool started to feel too clean. Real knowledge bases aren't
7 tidy documents, they're hundreds of interconnected ones, most genuinely
about the area you're working in without being what you need right now. I
built `X-RICH-1` on 15 candidates — the original 7 plus 8 new ones from the
same corpus — and needed more than "include/exclude" to classify them
honestly: artifacts the task absolutely needs (**MUST_INCLUDE**), artifacts
that help but aren't required (**ACCEPTABLE_OPTIONAL**), artifacts genuinely
connected to the domain but addressing a different concern
(**RELATED_BUT_UNNECESSARY** — latency SLOs, a change-freeze policy,
postmortems about a different incident, a saga-testing rule), artifacts
clearly out of scope (**MUST_EXCLUDE**), one artifact with no retrievable
content (**UNRESOLVABLE**), and `KN-101`, now **CONTESTED** — its decision is
captured and reported every run, but removed from the scored set before
scoring, so it can never move the score either way.

Both models retained all 3 required artifacts and excluded the genuinely
forbidden ones, every run. Jev's decisions were identical across all 5 of
its own runs — a fully deterministic fingerprint, mean score 0.683, zero
variance. GPT's mean score was 0.6794, ranging 0.665–0.683 across its 5 runs
(stddev ≈0.0072) — not identical run to run. GPT also wasn't internally
consistent with itself on which candidates it picked: across its 5 runs it
disagreed with Jev's fixed selection on one candidate (a postmortem) in all
5, and on a second (a saga-testing rule) in 4 of 5. So agreement between the
two models was 14 of 15 candidates on one GPT run, and 13 of 15 on the other
four — not a flat number, and not something I want to round off to "14/15
agreement" as if it held every time. `KN-101` was selected 5 of 5 times by
both, still fully excluded from the score. Both disagreements landed on
RELATED_BUT_UNNECESSARY candidates, never on a required or truly forbidden
one.

## Experiment 4 — Give the Worker the enterprise graph (`X-RICH-2`)

Narrower question: if you hand the model the actual structural information —
which apps depend on which — does that change anything? Everything about
`X-RICH-1` stayed fixed: same 15 candidates, same order, same candidate
bodies, same criterion, same TaskScope, same scorer, same providers. The only
addition was the complete, unfiltered application-dependency registry,
appended to every request.

Jev's scored metrics didn't move at all — same score, recall, precision, and
related-but-unnecessary rate, to the same decimal, with or without the
registry. GPT's did move: precision dropped from 0.557 to 0.478, and its
rate of admitting related-but-unnecessary candidates rose from 0.533 to
0.733. Recall stayed at 0.8 for both either way, and required/forbidden
behavior — the part that actually gates pass/fail — was unchanged. `KN-101`
remained selected 5/5 by both.

I want to be careful about the verb here. Adding the registry was
**associated with** a shift in GPT's selection behavior. The result is
**consistent with** the idea that explicit structural context can change how
liberally a model interprets "connected enough to include." It does not
establish that the registry **caused** the shift — one before/after
comparison, 5 repeats, one task, can't rule out other explanations, and it
doesn't tell me whether the same thing happens on a different task.

## Experiment 5 — Take context away (`X-RICH-3`)

This is the one that actually changed how I think about the whole problem,
and it came from a simple provocation: what if, instead of adding richness,
I take context away? `X-RICH-1` has 15 candidates. What if the Worker only
gets 5 slots?

That's a different kind of problem. Up to this point, every decision was
"should this one thing be in or out," judged independently. Once there's a
hard budget smaller than the number of things worth including, the question
changes shape — it's not "should this be included" anymore, it's "which five
deserve to survive."

To be precise about the mechanics, because this matters: I didn't change the
prompt or the criterion, and the models were never told a budget existed.
Each model still produced its normal, independent include/exclude decision
with a confidence value for all 15 candidates, exactly as in `X-RICH-1`. My
own aggregation code then ranked every "include" verdict by the model's own
stated confidence and mechanically kept the top 5. The models didn't choose
to respect a five-item budget — there was no budget in their prompt to
respect. The budget was imposed after the fact, by my code, on top of
decisions they'd already made independently.

Jev's ranking put the same 5 candidates on top in all 5 runs: all 3 required
items, `KN-101`, and exactly one related-but-unnecessary candidate. Recall
dropped from 0.8 to 0.6, precision rose from 0.571 to 0.75, score moved from
0.683 to 0.667. Zero variance across repeats.

GPT's selected top five varied across runs. It retained all three required
items in 3 of the 5 runs; in the other 2, a required artifact fell below the
cut line — the loyalty-account rule in one run, the domain-rules artifact in
the other — which tripped the required-item gate and produced a fail verdict
both times. Averaged across all 5 runs: recall 0.6, precision 0.66,
required-item retention 0.8667, mean score 0.5248.

I'm not going to say Jev is better than GPT here — that's not what this
measures. What I can say, narrower and more useful: under this specific
task, this specific candidate set, and this specific five-artifact budget,
Jev's confidence ranking was stable across repeats, while GPT's displaced a
required artifact in 2 of 5 runs.

Here's the idea that actually came out of running this: when context is
plentiful, selection can look like classification — is this thing in the
"yes" bucket or the "no" bucket. When context becomes scarce, selection
turns into prioritization — the system has to decide what to sacrifice, and
that decision exposes the ranking policy that was sitting underneath the
classifier the whole time, just never visible before, because there was
always room for everything. The question stops being "did the Worker
include the right things" and becomes "did the Worker protect the things it
couldn't afford to lose." Jev answered that the same way every time. GPT
answered it differently each time, and twice, what it gave up was something
it shouldn't have.

Context assembly is starting to look like resource allocation under
uncertainty, not just classification. I don't want to overstate that — five
runs on one task with one budget size is a pattern, not a law — but it's the
direction every one of these five experiments pushed me toward.

## `KN-101` — the full picture

| Experiment | `KN-101` treatment | Selection rate |
|---|---|---|
| `BC-0101` | `must_exclude` (frozen ground truth) | Jev 5/5, GPT 5/5 |
| `BC-0102` | `must_exclude` (frozen ground truth, necessity criterion) | Jev 2/5, GPT 5/5 |
| `X-RICH-1` | CONTESTED (excluded from scoring either way) | Jev 5/5, GPT 5/5 |
| `X-RICH-2` | CONTESTED | Jev 5/5, GPT 5/5 |
| `X-RICH-3` | CONTESTED, subject to the 5-item budget | Jev 5/5, GPT 2/5 |

`KN-101` has never gotten a resolved answer in this research, on purpose. Its
original ground-truth label conflicted with its actual content and with the
real enterprise dependency between Checkout and Pricing. It's structurally
connected (`APP-007` → `APP-003`), semantically plausible for the task, and
its task-specific necessity is still unresolved. I haven't changed the
historical benchmark ground truth, and I'm not using `KN-101` as evidence
that either model "failed" in some straightforward way — it's evidence that
the benchmark needed a second look.

## What I learned

1. **Relevance and necessity are different questions, and models answer them
   differently.** The same 7 candidates, the same models, produced a
   different `KN-101` outcome depending only on which question was asked.
2. **A benchmark can be wrong about its own distractor.** `KN-101`'s
   ground-truth label didn't match its actual content, and that mismatch
   survived undetected inside a passing-looking "fail" result until I
   actually read the artifact.
3. **Explicit structural context can shift selection behavior without
   changing the headline pass/fail outcome.** `X-RICH-2` didn't break
   anything and didn't fix anything — it moved GPT's precision and
   over-inclusion in a specific direction and did nothing measurable to Jev.
4. **Scarcity is what actually reveals a selection policy.** Everything
   before `X-RICH-3` could pass while quietly disagreeing on which
   related-but-unnecessary items to admit, because there was room for all of
   it. A hard budget forces a real trade-off.
5. **Context assembly is starting to look like resource allocation under
   uncertainty, not classification.** Every experiment pushed me further
   from "is this relevant" and closer to "given a limited budget and
   incomplete certainty about what's necessary, what gets kept."

I started by asking whether a Worker could retrieve the right information. I
ended up asking a harder question: when the Worker can't remember
everything, does it know what it can't afford to forget?

## Why Jev was useful

Not because it "won" anything — I'm not claiming Jev is a better model, a
better judge, or that its decisions are validated training data. What it
actually gave me:

- A structured decision interface — a typed question with an attached
  probability — instead of free-form text I then have to parse.
- Fast, cheap repeated decisions at the volume this kind of research needs.
  In `BC-0101`, its measured cost per run was roughly a hundred times lower
  than GPT's.
- A second, independently-built reasoning path on the same question, which
  is how I noticed the `BC-0102` divergence and the `X-RICH-3` stability
  difference in the first place. Two systems agreeing tells you something.
  Two systems disagreeing in a way that repeats tells you more.

That combination is why a future reinforcement-learning-from-contextual-
decisions (RLCD) pipeline seems worth exploring: task → candidates → Jev
decisions → feedback → decision dataset → improved selection policy. But
that's a future direction, not a result. What's observed here is that Jev is
cheap enough to make repeated decision generation practical. What's **not**
established is that Jev-generated decisions are good training signal for
anything — no experiment here tests label quality or trains a policy.

## What context actually costs

All GPT figures below are reconciled real costs from OpenAI's own usage
exports, matched by exact request count against each experiment's result
files — not the API's reported cost, which doesn't exist for the direct-API
transport used from `BC-0102` on. Full provenance:
[`GPT_COST_RECONCILIATION.md`](results/GPT_COST_RECONCILIATION.md).

| | BC-0102 (5×5 + validation) | X-RICH-1 (5×5) | X-RICH-2 (5×5) |
|---|---|---|---|
| Requests | 42 | 75 | 75 |
| Input tokens | 10,908 | 19,315 | 165,790 |
| Cached input tokens | 0 | 0 | 117,376 (≈71%) |
| Real cost | $0.011721 | $0.019951 | $0.032514 |
| Per repeat | ≈$0.00234 | ≈$0.00399 | ≈$0.00650 |

Raw input tokens jumped about 8.6× from `X-RICH-1` to `X-RICH-2` (the full
application registry, added to every call). Real cost rose only about 1.63×,
because roughly 71% of that added volume was identical repeated content,
billed at OpenAI's cached rate. Token growth isn't the same as cost growth
when the added content doesn't change between calls.

I don't have a reconciled cost figure for `X-RICH-3` yet, and I'm not
reporting a complete cross-experiment Jev cost comparison — `BC-0101` is the
only experiment where Jev's cost was captured directly rather than
reconstructed. Jev/GPT cost and latency aren't a fair capability comparison
anywhere in this project, because the transport and accounting path
differed between them (OpenRouter for both in `BC-0101`; Jev on OpenRouter
and GPT on direct OpenAI from `BC-0102` on).

## What I still don't know

- Everything here is one task, one domain. None of it generalizes to other
  tasks or domains without more work.
- Five repeats per condition is enough to notice a pattern, not enough for
  statistical significance — I haven't tested for it.
- `KN-101` is still contested. Not concluded necessary, not concluded
  unnecessary.
- `X-RICH-2` is consistent with the structural-context hypothesis. It
  doesn't establish causality or that it would replicate on another task.
- Transport/accounting changed between experiments (OpenRouter → direct
  OpenAI for GPT), so cost and latency aren't comparable across that
  boundary.
- `X-RICH-3` is one five-slot budget on one fifteen-candidate pool. I don't
  know if the stability difference holds at a different budget size or a
  larger sample.
- No evidence that Jev-generated decisions are good training labels for
  anything.
- No general claim that either model is "better" at context selection.
- No claim that more context is inherently harmful.

## Open questions

- Does the `KN-101` pattern — structural dependency, plausible semantic
  relevance, unresolved necessity — show up in other candidates, or is it
  specific to this one artifact?
- Would explicit `TaskScope` information (declared apps, code target —
  designed but never threaded into a live prompt, see `README.md`) change
  either model's `KN-101` or budget-induced behavior, independent of the
  changes already tested?
- Would GPT's run-to-run variance under a budget constraint persist at a
  larger sample size, or shrink toward Jev's observed stability?
- Is Jev's decision-generation speed/cost profile enough on its own to
  justify using it for large-scale synthetic-label generation, or does that
  need independent validation of decision quality first?

## Reproducibility

Everything above lives under `research/jev_context_decision/`: the benchmark
case (`benchmarks/examples/benchmark_case.example.json`), candidate
definitions (`candidates.py`, `experiment_3_candidates.py`), provider
integrations (`providers/`), the five experiment runners (`run_experiment.py`,
`run_experiment_3.py`, `run_experiment_x_rich_2.py`,
`run_experiment_x_rich_3.py`), the raw result files for every run reported
here (`results/*.json`), the offline test suite (`tests/`, 129 tests, no
network calls), the GPT cost reconciliation
(`results/GPT_COST_RECONCILIATION.md`), and this document. Every number in
this write-up was read from one of those files, not estimated. `RESULTS.md`
and `../EXPERIMENT_3_PROPOSAL.md` carry additional per-experiment detail for
`BC-0101` and `X-RICH-1` respectively.
