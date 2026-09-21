# SAT Symmetry Runtime Protocol v1

This protocol freezes the first wall-clock/runtime viability audit for SAT symmetry guidance.
It is an attribution and accounting protocol, not a solver speedup claim.

## Scope

The main question is:

> Does runtime degradation come from the weighted Glucose binary/input path, static GNN weights, event collection overhead, or adapter delta/inference?

The protocol does not train adapters, does not build a gate/selector, and does not claim speedup. Gate work starts only after a stable positive viability signal appears in specific family/scale strata.

## Solver Path

Main runtime v1 uses only:

- `solver_path_role=patched_pretrue_main`
- weighted Glucose preprocessing enabled by the patched `pre=true` path
- no `--weighted-no-pre`

The `--weighted-no-pre` path is a diagnostic appendix only:

- `solver_path_role=weighted_no_pre_diagnostic`
- used to isolate preprocessing effects
- excluded from main runtime tables, bootstrap CIs, and viability statements

## Methods

Method order is fixed:

1. `plain_unguided_glucose`
2. `neutral_weighted_glucose`
3. `static_weighted_glucose`
4. `cached_trace_no_adapter_final`
5. `event_adapter_final`

`neutral_weighted_glucose` uses the weighted binary/input path with uniform variable weights. It is not bit-identical to plain Glucose; it isolates weighted solver path cost before learned weights are introduced.

`cached_trace_no_adapter_final` pays static inference, warmup rollout, event extraction, and event feature attach. Its final solve reuses the static weighted final solve and does not run adapter inference.

## Attribution Matrix

All deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

| Delta | Definition | Interpretation |
| --- | --- | --- |
| `weighted_binary_input_delta` | `neutral_weighted_glucose - plain_unguided_glucose` | weighted binary / weighted input path cost |
| `static_weights_delta` | `static_weighted_glucose - neutral_weighted_glucose` | static GNN weights effect |
| `event_collection_overhead_delta` | `cached_trace_no_adapter_final - static_weighted_glucose` | warmup rollout + event extraction/attach overhead |
| `adapter_delta_inference_delta` | `event_adapter_final - cached_trace_no_adapter_final` | adapter delta plus adapter inference |

Each delta is reported for final CPU time, protocol accounted time, final decisions, and final conflicts where available.

## Pairing And Bootstrap Unit

The statistical unit is `base_instance_id`.

Permutation variants and repeats are nested observations for the same base instance. They can measure runtime stability and permutation consistency, but they are not independent examples. Bootstrap/CI summaries first aggregate within base instance, then resample base instances.

If Glucose random seeds do not materially affect these runs, repeat analysis should be described as repeated runtime stability, not seed stability.

## Manifest Strata

The runtime v1 manifest must include:

- `family`
- `base_instance_id`
- `variant`
- `symmetry_strength`: `strong`, `weak`, or `none`
- `control_type`: `strong_symmetry`, `weak_symmetry`, or `non_symmetric_control`
- `scale`: `small`, `medium`, `large`, or `stress`
- `scale_key`
- `benchmark_role`: `main`, `control`, or `static_only_stress`
- `family_scale`
- `event_audit_role`

Strong symmetry, weak symmetry, and non-symmetric controls are reported separately. Permutation variants only support same-base stability checks.

## Metrics

Required per-method metrics:

- `final_result`
- `final_solved`
- correctness on known SAT/UNSAT rows only
- `final_cpu_time`
- `final_wall_time`
- `protocol_accounted_time`
- `protocol_wall_time`
- final decisions, conflicts, propagations, restarts
- static inference wall time
- warmup CPU/wall time
- event attach wall time
- adapter inference wall time
- event availability and event-state nonzero summaries
- graph gate evidence/open flag

Required output tables:

- per-instance method rows
- phase accounting rows
- by-family summary
- by-base-instance summary
- attribution rows
- attribution by base
- timeout/correctness summary
- paired bootstrap/CI summary by base instance

## Timeout And Correctness Policy

The final CPU cap is the only main solve timeout cap. Warmup uses its own CPU/conflict budget and is accounted as event collection overhead.

Rows with `INDETERMINATE` or no SAT/UNSAT result are counted as unsolved under the cap. Correctness is reported separately and only for rows with known expected `SATISFIABLE` or `UNSATISFIABLE`; `UNKNOWN` rows are excluded from correctness rates.

## Pilot Policy

Pilot runs are protocol sanity checks only. They may use a small number of base instances to calibrate:

- CPU cap
- timeout policy behavior
- event collection availability
- output schemas
- bootstrap script compatibility

Pilot results must not be used as runtime conclusions.

## Full Wall-Clock v1

The full run should use the v1 manifest and main `patched_pretrue_main` path. Report viability and attribution evidence by:

- overall
- family
- control type
- scale
- family/scale
- base instance

Do not merge diagnostic `weighted_no_pre_diagnostic` rows into the main result tables.
