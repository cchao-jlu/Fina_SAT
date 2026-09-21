# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_stress_manifest.csv`
- event-role rows: `2` distinct CNFs
- repeats: `1`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `2.0` seconds
- warmup CPU limit: `2.0` seconds
- warmup conflict limit: `20`
- trace LBD threshold: `2`
- neutral weighted baseline: phase `1.0`, weight `1.0`

## Method Semantics

- `plain_unguided_glucose`: plain Glucose final solve, no weighted input path and no model inference.
- `neutral_weighted_glucose`: weighted Glucose binary with all variables assigned the same phase/weight.
- `static_weighted_glucose`: W0.5 checkpoint static/base guidance, then weighted Glucose final solve.
- `cached_trace_no_adapter_final`: pays static inference, event-collecting warmup, and event attach; the final solve reuses the static guidance and does not run adapter inference.
- `event_adapter_final`: pays static inference, event-collecting warmup, event attach, adapter inference, and weighted Glucose final solve.

`neutral_weighted_glucose` is not bit-identical to plain Glucose. It isolates the
weighted binary / weighted input parsing path from the learned static and event weights.

`cached_trace_no_adapter_final` is the required ablation for separating event collection cost
from the adapter's effect on final variable weights.

Permutation variants are not treated as independent evidence in the attribution tables;
those summaries are grouped by `base_instance_id`.

## Artifacts

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_attribution.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/tmp_symmetry_solver_protocol_preflight_guided_loss_diagnostics.csv`

## Coverage

| family | instances | base_instances |
| --- | --- | --- |
| php | 2 | 2 |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 2 | 2 | 2 | 2 | 2 | 0 | 0.001149 | 0.001149 | 0.001149 | 0 | 0 |
| neutral_weighted_glucose | 2 | 2 | 2 | 2 | 2 | 0 | 0.002271 | 0.002271 | 0.002271 | 0 | 0 |
| static_weighted_glucose | 2 | 2 | 2 | 2 | 2 | 0 | 0.01876 | 0.01876 | 0.0007935 | 0 | 0 |
| cached_trace_no_adapter_final | 2 | 2 | 2 | 2 | 2 | 2 | 0.02107 | 0.02107 | 0.0007935 | 0.001422 | 0 |
| event_adapter_final | 2 | 2 | 2 | 2 | 2 | 2 | 0.02347 | 0.02347 | 0.001794 | 0.001422 | 0.001408 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 4 | 4 | 4 | 0.001422 | 0.0008819 | 0.0007038 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 2 | 2 | 1 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | event_overhead_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | 1 | 1 | 1 | 0 | 0 | 0 | 0.001025 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 1 | 1 | 1 | 0 | 0 | 0 | 0.003582 | 28 | 20 | 1 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| php | plain_unguided_glucose | 2 | 2 | 0.001149 | 0.001149 | 0 | 0 |
| php | neutral_weighted_glucose | 2 | 2 | 0.002271 | 0.002271 | 0 | 0 |
| php | static_weighted_glucose | 2 | 2 | 0.01876 | 0.0007935 | 0 | 0 |
| php | cached_trace_no_adapter_final | 2 | 2 | 0.02107 | 0.0007935 | 0.001422 | 2 |
| php | event_adapter_final | 2 | 2 | 0.02347 | 0.001794 | 0.001422 | 2 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
