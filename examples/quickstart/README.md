# Quickstart — run a Worker against a benchmark case

Run a tiny reference Worker against a real EnterpriseSim benchmark case and see an
objective score, in one command. **No dependencies. No API key. Deterministic.**

```bash
python examples/quickstart/run_quickstart.py
```

Expected output:

```
==================================================================
EnterpriseSim quickstart — BC-0101 (BENCH-01)
  Context assembly for guest checkout (CHK-1421)
==================================================================
Worker included : ['EXP-055', 'EXP-090', 'KN-045', 'KN-052']
------------------------------------------------------------------
  hard gate        : PASS
  retrieval recall : 0.8
  retrieval precis.: 1.0
  objective score  : 0.79  (pass ≥ 0.8, partial ≥ 0.6)
  VERDICT          : PARTIAL
==================================================================
```

## What just happened

1. **Loaded a frozen benchmark case** — `BC-0101` from
   [`benchmarks/examples/benchmark_case.example.json`](../../benchmarks/examples/benchmark_case.example.json).
   The task: assemble the right context for the guest-checkout story `CHK-1421` —
   include the decisive facts, exclude the distractors, stay in budget.
2. **A baseline Worker produced a `ContextObject`** — `StubContextWorker` picks corpus
   items by naive keyword relevance. (This is the piece you replace.)
3. **Scored with the case's own recipe** — `objective_first`: a hard gate (all required
   items present, forbidden absent) plus `retrieval_recall` and `retrieval_precision`,
   weighted exactly as the case declares, then checked against the pass/partial thresholds.

## The point

The stub scores **0.79 — PARTIAL**, just under the 0.80 pass bar. That's your baseline
to beat. Swap `StubContextWorker.assemble()` for your own model-backed logic — following
the SDK contracts in [`../../sdk/`](../../sdk/) — and re-run to see whether your agent
clears the bar. Same task, any model underneath.

## Notes

- The quickstart keeps a tiny local topic catalog so it has zero dependencies; the real
  corpus items (`KN-###`, `EXP-###`) are full objects under
  [`../../enterprise/`](../../enterprise/) and [`../../corpus/`](../../corpus/).
- It scores the objective metrics only; the case also defines a model-assisted
  `composition_quality` rubric item (ordering, provenance, budget discipline) that a
  full runtime would evaluate.
