# Decision Intelligence

> **Proprietary — Bytesurge Runtime research. Not part of EnterpriseSim; not Apache-2.0.**
>
> This document designs a core Bytesurge algorithm. It is proprietary and is **not** governed
> by EnterpriseSim's Apache-2.0 license. See [`NOTICE.md`](NOTICE.md).

| Field | Value |
|---|---|
| Satisfies (EnterpriseSim contract) | `sdk.decision.Orchestrator` — the control loop (`interpret` / `decide` / `trace`) |
| Supporting types | `sdk.decision.Control`, `sdk.decision.ConfidencePolicy`, `sdk.decision.PolicyGuard`, `sdk.decision.PolicyVerdict` |
| Architecture reference | `ARCH-06` (Decision Intelligence) |
| Protocol reference | `RFC-0007` (DI Control Loop); confidence per `RFC-0009`; sole-orchestrator `ADR-0008`, confidence-gated autonomy `ADR-0014`, mandatory trace `ADR-0021` |
| Status | Research — design only |

---

## 1. Problem statement

`ARCH-06` makes Decision Intelligence the **sole orchestrator** of the ECL — the only layer with
agency (`ADR-0008`). `RFC-0007` fixes its contract: `sdk.decision.Orchestrator` with exactly three
methods — `interpret(trigger, context_hint) -> TaskIntent`, `decide(plan, context, evaluation) ->
DecisionObject`, and `trace(run_id) -> Sequence[DecisionObject]` — driving the loop
**Interpret → Plan → Route → Reason → Act → Evaluate → Decide**. Each `decide` turn must emit an
immutable `DecisionObject` whose `choice` is a `Control` value (`proceed`, `re-retrieve`, `replan`,
`retry`, `escalate`, `abort`), carrying a fused confidence, a rationale, and the per-layer
confidences fused (`ADR-0021`). Bytesurge must design the **control policy** that lives inside
`decide` — the logic that turns `(plan, context, evaluation)` into the next `Control`.

The contract fixes the loop's *shape* and delegates the pieces: planning to `RFC-0008`, confidence
math to `sdk.decision.ConfidencePolicy` (`RFC-0009`), model selection to the Router (`RFC-0010`),
guardrails to `sdk.decision.PolicyGuard` (`RFC-0030`). What remains open — and what Bytesurge owns —
is the **orchestration algorithm** that sequences these under three hard constraints from `ARCH-06`:

1. **Confidence-gated autonomy** (`ADR-0014`) — never take a high-stakes action at low fused
   confidence; fuse per-layer confidences and map `(fused, risk_tier)` to `Control` via
   `ConfidencePolicy` (`RFC-0009`), consuming Evaluation's **judgment** (not outcome) confidence
   (`ADR-0017`).
2. **Policy as a hard gate, not a vote** (`ADR-0041`) — a `PolicyGuard` block forces `escalate`/
   `abort` regardless of confidence (Tier 0/PCI two-approval rule, `CANON-001` §7).
3. **Bounded, auditable termination** — the loop must halt on success, escalation, iteration/
   reasoning-budget exhaustion, or diminishing returns (`RFC-0007` §4.5), and every choice must land
   on the immutable trace (`ADR-0021`) so runs are replayable (`RFC-0024`) and reflectable (`RFC-0016`).

This must remain **model-agnostic** (`ARCH-07`; all model access via the Gateway) and **domain-
agnostic** — the same `Orchestrator` drives a Checkout Worker and a Recruitment Worker (`ARCH-06`
Example C). The `CHK-1421` guest-checkout loop (Tier 0, `PLAN-0072`, `EXP-090`, fused 0.90 → proceed;
and the Example-B partial → re-retrieve → replan → proceed) is the touchstone.

---

## 2. Approaches

Five named approaches to the control policy inside `decide` / the loop driver.

### 2.1 Rule/policy finite-state machine (FSM)

Encode the `ARCH-06` lifecycle directly as an explicit state machine: states
`{Interpreting, Planning, Routing, Reasoning, Acting, Evaluating, Deciding}` with transitions
driven by `control_for(fuse(inputs), risk_tier)` and the `PolicyGuard` verdict. Deterministic,
trivially auditable, maps 1:1 to `RFC-0007` §3.2. Transitions are pure functions of
`(fused_confidence, risk_tier, policy_verdict, verdict, budget_remaining)`. This is the transparent
baseline and the reference the others are measured against.

### 2.2 Behavior trees

Structure control as a behavior tree (BT) of sequence/selector/decorator nodes: a selector tries
`proceed` → falls back to `re-retrieve` → `replan` → `retry` → `escalate` → `abort`; decorators
enforce budgets (max-iterations, cost caps) and confidence gates as guard conditions. BTs are modular
and composable — new recovery behaviors (a new re-retrieval strategy) slot in as subtrees without
rewriting the loop, and they remain fully inspectable. Widely used in robotics/game AI for exactly
this "reactive control under guards" shape.

### 2.3 Planning (HTN / PDDL-style)

Treat orchestration as automated planning: the goal (`success_criteria`) and operators (context-
assemble, reason, act, evaluate) are given to an HTN or PDDL-style planner that produces and repairs
the step sequence. `replan` becomes plan-repair. Powerful for tasks with rich sub-goal structure and
strong at producing explicit, ordered plans — but note the ECL already delegates *plan construction*
to the Planner (`RFC-0008`); here planning would govern the *meta*-control (which control action to
take), which is heavier than the problem needs for a fixed six-`Control` action space.

### 2.4 RL control policy

Learn a policy `π(control | state)` over the state `[fused_confidence, per-layer confidences,
risk_tier, verdict, iterations_used, cost_used, replan_count]` from historical runs, rewarding
successful low-cost completions and penalizing failed autonomy, wasted iterations, and missed
escalations. Trained offline on the EnterpriseSim decision-trace + EVAL corpus (learning outside the
model, `ADR-0003`). Can learn subtle policies — e.g. that a second `re-retrieve` rarely helps on a
given task type, so escalate sooner (diminishing-returns detection, learned). Optimizes the
cost/quality/latency trade `ARCH-06` cares about.

### 2.5 LLM-as-controller with guardrails

Use a model to propose the next `Control` given a structured summary of `(plan, context, evaluation,
budget)`, then **constrain** it: the proposal is only advisory and is intersected with the
deterministic `ConfidencePolicy` + `PolicyGuard` gates, which can only ever *subtract* autonomy
(`ADR-0041`). Flexible on messy, novel situations where hand-written rules are brittle; but an LLM
controller is opaque, non-reproducible, and risks the very "opaque decisions" failure `ARCH-06`
forbids unless every proposal is gated and traced. Cannot be the *authority* — only a *proposer*
under hard gates.

---

## 3. Trade-offs

| Approach | Auditability | Adaptivity | Training data | Reproducible | Safety (gating fit) | Cost/latency |
|---|---|---|---|---|---|---|
| Rule FSM | **Excellent** | Low | None | **Yes** | **Excellent** | Very low |
| Behavior tree | **Excellent** | Medium | None | **Yes** | **Excellent** | Very low |
| HTN/PDDL planning | High | Medium–high | Domain model | Yes | High | Medium (planning cost) |
| RL policy | Low–medium | **High** | Needs trace+EVAL corpus | Yes (fixed policy) | Needs guard wrapper | Low (inference) |
| LLM-as-controller | **Poor** (opaque) | **Highest** | Pretrained | **No** | Needs hard gate | High (model call/turn) |

Cross-cutting tensions:

- **Adaptivity vs. auditability.** The more learned/generative the controller, the better it handles
  novelty and the harder it is to explain — a direct conflict with `ADR-0021`'s mandatory trace and
  `ARCH-06`'s "opaque decisions" failure mode. The gate wrapper is what reconciles them.
- **Confidence-gating must be deterministic regardless of controller.** Whatever proposes the next
  control, the *authority* is `ConfidencePolicy.control_for` + `PolicyGuard` (`RFC-0009` §4.4,
  `ADR-0041`). This is non-negotiable: gating is where safety lives, so it cannot be delegated to a
  learned or generative component.
- **Analysis paralysis vs. premature action.** Looser looping raises quality but risks the
  never-terminates failure; tighter budgets risk acting too soon. Diminishing-returns detection and
  per-tier iteration budgets (`RFC-0007` §4.5) are the balance.
- **Fixed vs. learned thresholds.** `RFC-0009` §4.4 bands are illustrative and expected to be tuned/
  learned; a learned threshold set is better calibrated but can drift and demands ongoing calibration
  (`RFC-0009` §4.6).

---

## 4. Advantages

- **Confidence-gated by construction.** Routing every control decision through
  `fuse → control_for → intersect(PolicyGuard)` makes `ADR-0014` structural: high-stakes actions
  cannot proceed at low fused confidence, and a policy block always wins (`ADR-0041`).
- **Judgment-confidence correctness.** Consuming Evaluation's `judgment_confidence` (not
  `outcome_confidence`) into `fuse` (`ADR-0017`, `RFC-0009` §4.5) means the loop acts on *how
  trustworthy the verdict is*, not how flattering — a `partial` at high judgment confidence correctly
  drives `replan`, a `pass` at low judgment confidence correctly drives confidence-raising first.
- **Bounded and terminating.** Explicit iteration/reasoning budgets + diminishing-returns detection
  guarantee halting and directly mitigate the analysis-paralysis failure (`RFC-0007` §4.5).
- **Fully auditable.** Every turn emits an immutable `WorkerDecision` with `choice`, `rationale`,
  `fused_confidence`, and the `inputs` map — the trace *is* the decisions, not a lossy summary
  (`ADR-0021`), enabling replay (`RFC-0024`) and reflection (`RFC-0016`).
- **Model- and domain-agnostic.** Heavy delegation (planning, routing, execution, scoring, policy
  behind stable contracts) keeps the same `Orchestrator` driving any Worker type with only intent,
  tools, policies, and rubrics differing (`ARCH-06` Example C, `ADR-0008`).
- **Cost-aware routing.** Difficulty-estimated model routing via the Router/Gateway spends
  high-reasoning models only where warranted (`ARCH-06` routing efficiency signal).

---

## 5. Weaknesses

- **Concentration risk.** As the sole agent (`ADR-0008`), a control-loop defect affects every Worker
  type; mitigated by the narrow three-method contract and heavy delegation (`RFC-0007` §5).
- **Serialization overhead.** An inspectable per-turn loop with a decision + trace entry each turn is
  slower and chattier than one opaque model call (`RFC-0007` §5); bounded by `RFC-0029` budgets.
- **Rigidity on trivial work.** A fixed loop feels heavy for Tier 3 tasks; partly offset by looser
  low-tier `control_for` thresholds (`RFC-0009` §4.4), but a purely rule/BT controller can still
  over-ceremony simple tasks.
- **Calibration burden.** Confidence-gated autonomy is only as good as threshold calibration; stale
  thresholds drift toward over- or under-caution and silently re-create overconfident autonomy
  (`RFC-0009` §4.6). Requires continuous control-decision-accuracy tracking.
- **Learned-controller drift & opacity.** Any RL/LLM component risks unexplainable or miscalibrated
  choices; usable only as a *proposer* under deterministic gates, never as the authority.
- **Diminishing-returns detection is heuristic.** Deciding a second `re-retrieve` "won't help" is an
  estimate; too eager escalates needlessly, too lax paralyzes.

---

## 6. Computational complexity

Let `I` = loop iterations for a task (bounded by the iteration budget), `L` = ECL layers fused
(4: context, knowledge, experience, evaluation), `A` = candidate control actions (6 `Control`
values), `T` = trace length (= number of decisions, `≤ I`).

| Operation | Complexity | Notes |
|---|---|---|
| `interpret` | `O(1)` model call | One structured extraction; no work committed. |
| `fuse(inputs)` | `O(L)` | Weakest-link combiner over the 4 inputs (`RFC-0009` §4.3). |
| `control_for(fused, tier)` | `O(1)` | Threshold-band lookup. |
| `PolicyGuard.check` | `O(g)` for `g` guardrails | Approvals, PCI, SoD, fairness checks. |
| `decide` (one turn) | `O(L + g)` | Fusion + gate + policy intersection + emit. |
| Loop over a task | `O(I · (L + g + C_step))` | `C_step` = delegated cost of context/reason/act/eval that turn. |
| `trace(run_id)` | `O(T)` | Return the ordered append-only decision sequence. |
| Trace append | `O(1)` amortized | Immutable append with monotonic `trace_seq`. |
| RL policy inference (if used) | `O(state_dim)` per turn | Cheap forward pass; training is offline `O(runs)`. |
| LLM proposer (if used) | `O(1)` model call per turn | Dominant per-turn cost; why it is optional. |

The orchestration logic itself is negligible (`O(L + g)` per turn); the real cost is `C_step` — the
delegated layer work — and the number of iterations `I`. Bounding `I` (iteration/reasoning budget,
`RFC-0007` §4.5, `RFC-0029`) is therefore the primary lever on total task cost. A learned policy that
escalates on diminishing returns *reduces* `I`, so it pays for its own inference.

---

## 7. Enterprise scalability

**Throughput & latency.** A Fortune-500 fleet runs many thousands of concurrent Worker runs. The
orchestrator is nearly stateless per turn (`decide` is a pure function of its arguments plus the
budget counters), so it scales horizontally without coordination — each run is independent and
shard-free. Per-turn orchestration overhead is sub-millisecond; end-to-end latency is dominated by
the delegated layer calls (context assembly, model reasoning, execution, evaluation), not by DI.

**Trace storage & sharding.** The immutable decision trace is append-only and partitioned by
`run_id`; at fleet scale traces are the dominant DI storage cost. They shard trivially by run/tenant,
are write-once (no updates, `ADR-0021`), and tier to cold storage after the reflection/audit window
(retention deferred to `RFC-0023`). Because a `WorkerDecision` mirrors `DecisionObject` field-for-
field, traces are self-describing and need no join to be replayed (`RFC-0024`).

**Model routing at scale.** Difficulty-estimated routing (`RFC-0010`) is the main cost lever:
sending Tier 3 trivia to a cheap model and reserving high-reasoning models for Tier 0 subtle-risk
changes (as `PLAN-0072` does) keeps aggregate inference spend proportional to actual difficulty.
Speculative routing (`RFC-0007` §9 — cheap and high-reasoning in parallel, decide on evaluated
results) is an available latency/cost optimization under `RFC-0029`.

**Budget governance.** Iteration and reasoning budgets (`RFC-0029`) cap worst-case per-task cost and
guarantee termination, so fleet cost is bounded and predictable even under adversarial tasks — no run
can loop forever consuming tokens.

**Incremental improvement.** Control-decision accuracy (`ARCH-06` signal) feeds the Learning Engine
(`ARCH-05`), which recalibrates `control_for` thresholds per task type on a batch cadence — never in
the hot path, and always subject to `RFC-0009` calibration validation before a threshold change is
accepted. Per-tenant threshold sets and calibration curves keep autonomy tuned per customer without
cross-tenant leakage.

**Multi-Worker orchestration (future).** `ARCH-06`/`RFC-0007` §8 anticipate one `run_id` coordinating
several specialized Workers; the stateless-per-turn design and per-decision attribution
(`worker` + `trace_seq`) extend to interleaved traces without changing the core loop.

---

## 8. Explainability

The mandatory decision trace is the audit surface, and the design makes every choice
self-explaining.

- **Per-decision rationale.** Every `WorkerDecision` carries `choice`, a non-empty `rationale`,
  `fused_confidence`, and the full `inputs` map of per-layer confidences (`RFC-0007` §4.3) — so an
  auditor sees *exactly which numbers produced which control action* on every turn. The `CHK-1421`
  proceed reads: `choice=proceed, fused=0.90, inputs={context 0.86, knowledge 0.95, experience 0.91,
  eval_judgment 0.88}, rationale="all success_criteria met; Tier 0 threshold cleared; policy allowed"`.
- **Gate attribution.** When `control_for` returns a confidence-raising or escalating control, the
  trace records the binding constraint — the tighter Tier 0/PCI threshold, or the weakest-link input
  that capped the fused value (`RFC-0009` §4.3). Example B's `re-retrieve` reads `capped by
  eval_judgment drop after APP-012 contract fail`.
- **Policy verdict on the trace.** A `PolicyGuard` block is recorded as the `policy_verdict` on the
  decision (`allowed=false, reason="Tier 0 change missing 2nd approval", requires_human=true`),
  making a *policy* stop distinguishable from a *confidence* stop — the difference an auditor most
  needs (`ADR-0041`).
- **Judgment-vs-outcome clarity.** Because DI fuses `judgment_confidence` and the trace records it as
  such, an auditor can see the loop escalated a flattering-but-shaky `pass` rather than acting on it
  (`ADR-0017`, `RFC-0009` §4.5) — the subtle correctness the model exists to guarantee.
- **Replayability.** The trace + frozen `ContextObject` (`ADR-0011`) + plan lineage make a run
  deterministically replayable (`RFC-0024`); reflection (`RFC-0016`) reconstructs *why* the Worker did
  what it did, and no execution may exist without a decision explaining it (`RFC-0007` §4.4).

---

## 9. Recommendation

Bytesurge should adopt a **guarded behavior-tree / FSM controller with deterministic confidence-and-
policy gates, extensible to a learned proposer**:

1. **Core driver: an explicit behavior tree over the `ARCH-06` lifecycle** (equivalently a rule FSM).
   A selector tries `proceed → re-retrieve → replan → retry → escalate → abort`; decorators enforce
   the iteration/reasoning budgets and diminishing-returns detection as guard conditions
   (`RFC-0007` §4.5). BTs are chosen over a flat FSM for modular recovery subtrees, but both are fully
   deterministic and auditable — the property `ADR-0021` demands.
2. **Authority stays deterministic.** The next `Control` is always the intersection of
   `ConfidencePolicy.control_for(fuse(inputs), risk_tier)` (weakest-link, honest, risk-adaptive —
   `RFC-0009`) with `PolicyGuard.check` (hard gate, subtract-only — `ADR-0041`). DI fuses Evaluation's
   **judgment** confidence, never outcome (`ADR-0017`). This gate is non-negotiable regardless of what
   proposes the action.
3. **Fuse honestly.** Use a weakest-link/product-style combiner (never an arithmetic mean, which
   `RFC-0009` §4.3 rules non-conforming) so starved context cannot be laundered by strong knowledge.
4. **Bound and trace everything.** Per-tier iteration + reasoning budgets guarantee termination and
   escalate on exhaustion (mitigating analysis paralysis); every turn appends an immutable
   `WorkerDecision` with rationale, fused confidence, inputs, and any `policy_verdict`.
5. **Learn at the edges, not the center.** Graduate the *thresholds* (`control_for` bands) and the
   *diminishing-returns / re-retrieve-vs-escalate* heuristic to Learning-Engine-tuned, per-task-type
   values calibrated against control-decision accuracy (`RFC-0009` §4.6, `ARCH-06` future) — learning
   outside the model (`ADR-0003`). Optionally admit an **LLM-as-controller only as an advisory
   proposer** for novel situations, whose suggestion is always intersected with the deterministic
   gates and can only subtract autonomy.

**Why this hybrid.** It keeps the safety-critical decision — *may this Worker act autonomously?* —
deterministic, calibrated, and fully traced (`ADR-0014`, `ADR-0021`, `ADR-0041`), which is the
entire reason `ARCH-06` concentrates agency in one inspectable orchestrator. It gains adaptivity
where adaptivity is safe (tunable thresholds, modular recovery subtrees, an optional gated proposer)
without ever letting a learned or generative component *authorize* a high-stakes action. It honors
the three-method `Orchestrator` contract and every delegation boundary, stays model- and domain-
agnostic (`ARCH-07`, `ADR-0008`), and produces the decision trace that makes Worker behavior
benchmarkable on EnterpriseSim's open suites — the open benchmark grading the proprietary runtime.
