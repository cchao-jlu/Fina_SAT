# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_manifest.csv`
- event-role rows: `14` distinct CNFs
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
- weighted solver no-pre: `False`
- solver path role: `patched_pretrue_main`

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

`patched_pretrue_main` is the main patched weighted Glucose path. `weighted_no_pre_diagnostic` is only a diagnostic path for isolating preprocessing effects; do not merge it with the main runtime protocol.

Permutation variants are not treated as independent evidence in the attribution tables;
those summaries are grouped by `base_instance_id`.

## Artifacts

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_pilot_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 6 | 6 | non_symmetric_control | large,medium | control | none |
| subset_cardinality | 3 | 3 | weak_symmetry | large,medium | main | weak |
| vertex_cover_torus | 5 | 5 | strong_symmetry | large,medium | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 14 | 14 | 8 | 8 | 14 | 0 | 0.1542 | 0.003514 | 0.1542 | 0 | 0 |
| neutral_weighted_glucose | 14 | 14 | 8 | 8 | 14 | 0 | 0.2158 | 0.004733 | 0.2158 | 0 | 0 |
| static_weighted_glucose | 14 | 14 | 8 | 8 | 14 | 0 | 0.3798 | 0.02989 | 0.215 | 0 | 0 |
| cached_trace_no_adapter_final | 14 | 14 | 8 | 8 | 14 | 14 | 0.5973 | 0.03412 | 0.215 | 0.2166 | 0 |
| event_adapter_final | 14 | 14 | 8 | 8 | 14 | 14 | 0.5992 | 0.03349 | 0.2154 | 0.2166 | 0.001567 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 28 | 28 | 28 | 0.2166 | 0.0009304 | 0.0007836 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 14 | 14 | 1 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 0.06151 |
| weighted_binary_input_delta_protocol_time | 0.06151 |
| static_weights_delta_final_cpu | -0.0007114 |
| static_weights_delta_protocol_time | 0.164 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.2175 |
| adapter_delta_inference_delta_final_cpu | 0.0003677 |
| adapter_delta_inference_delta_protocol_time | 0.001935 |
| adapter_inference_wall_time | 0.001567 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | 0.001548 | 0.001548 | -0.001146 | 0.03094 | 0 | 0.006933 | -0.003023 | -0.0006386 | 0.002385 |
| non_symmetric_control | medium | -0.0009107 | -0.0009107 | -0.000623 | 0.02202 | 0 | 0.003156 | -0.0008603 | 0.0005618 | 0.001422 |
| strong_symmetry | large | 0.2735 | 0.2735 | 0.003154 | 0.677 | 0 | 0.9882 | 0.009282 | 0.01058 | 0.001296 |
| strong_symmetry | medium | 0.0195 | 0.0195 | -0.005541 | 0.02465 | 0 | 0.02144 | -0.005721 | -0.004439 | 0.001282 |
| weak_symmetry | large | -0.0001455 | -0.0001455 | -0.001705 | 0.0192 | 0 | 0.002591 | 0.0001095 | 0.001479 | 0.00137 |
| weak_symmetry | medium | 2.8e-05 | 2.8e-05 | 0.000377 | 0.01911 | 0 | 0.002386 | 0.000176 | 0.001503 | 0.001327 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v100_c600_seed1914 | 1 | 1 | 1 | 0 | 0 | 0 | -0.000632 | 0.04515 | 0.01202 | -0.0006545 | 181 | 157 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 1 | 1 | 1 | 0 | 0 | 0 | 0.000317 | 0.01857 | 0.001947 | 0.002919 | 14 | 13 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v35_c149_seed1911 | 1 | 1 | 1 | 0 | 0 | 0 | -0.001918 | 0.02207 | 0.004705 | 0.001351 | 14 | 7 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 1 | 1 | 1 | 0 | 0 | 0 | -0.001131 | 0.02543 | 0.002817 | -0.002585 | 10 | 0 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | 1 | 1 | 1 | 0 | 0 | 0 | 0.001589 | 0.0225 | 0.005268 | 9.511e-06 | 19 | 6 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v80_c340_seed1913 | 1 | 1 | 1 | 0 | 0 | 0 | 0.003687 | 0.02515 | 0.003506 | -0.001271 | 23 | 2 | 1 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 1 | 1 | 1 | 0 | 0 | 0 | 0.00018 | 0.0176 | 0.001451 | 0.001762 | 174 | 152 | 1 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 1 | 1 | 1 | 0 | 0 | 0 | -0.000471 | 0.0208 | 0.003731 | 0.001197 | 384 | 312 | 1 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 1 | 1 | 1 | 0 | 0 | 0 | 2.8e-05 | 0.01911 | 0.002386 | 0.001503 | 84 | 69 | 1 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 1 | 1 | 1 | 0 | 0 | 0 | 0.02063 | 0.02069 | 0.01493 | -0.002937 | 4 | 5 | 1 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 1 | 1 | 1 | 0 | 0 | 0 | 0.01836 | 0.02862 | 0.02794 | -0.00594 | 6 | 7 | 1 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 1 | 1 | 1 | 0 | 0 | 0 | 0.297 | 0.1124 | 0.3397 | 0.02495 | 7 | 8 | 1 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 1 | 1 | 1 | 0 | 0 | 0 | 0.5335 | 0.1504 | 0.6302 | 0.005893 | 12 | 12 | 1 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | 1 | 1 | 1 | 0 | 0 | 0 | -0.00998 | 1.768 | 1.995 | 0.0008949 | 11 | 12 | 1 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | plain_unguided_glucose | 6 | 6 | 0.003525 | 0.003525 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 6 | 6 | 0.003844 | 0.003844 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 6 | 6 | 0.03032 | 0.002959 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 6 | 6 | 0.03537 | 0.002959 | 0.003814 | 6 |
| random_3sat_control | event_adapter_final | 6 | 6 | 0.03533 | 0.001018 | 0.003814 | 6 |
| subset_cardinality | plain_unguided_glucose | 3 | 3 | 0.002585 | 0.002585 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 3 | 3 | 0.002498 | 0.002498 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 3 | 3 | 0.02167 | 0.001487 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 3 | 3 | 0.02419 | 0.001487 | 0.001809 | 3 |
| subset_cardinality | event_adapter_final | 3 | 3 | 0.02568 | 0.001618 | 0.001809 | 3 |
| vertex_cover_torus | plain_unguided_glucose | 5 | 5 | 0.4261 | 0.4261 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 5 | 5 | 0.598 | 0.598 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 5 | 5 | 1.014 | 0.5977 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 5 | 5 | 1.616 | 0.5977 | 0.6008 | 5 |
| vertex_cover_torus | event_adapter_final | 5 | 5 | 1.62 | 0.601 | 0.6008 | 5 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
