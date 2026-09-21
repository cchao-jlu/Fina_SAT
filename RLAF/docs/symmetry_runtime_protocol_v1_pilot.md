# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_manifest.csv`
- event-role rows: `7` distinct CNFs
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_pilot_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | 1 | 1 | weak_symmetry | medium | main | weak |
| php | 2 | 2 | strong_symmetry | small | main | strong |
| random_3sat_control | 3 | 3 | non_symmetric_control | medium,small | control | none |
| subset_cardinality | 1 | 1 | weak_symmetry | medium | main | weak |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 7 | 7 | 3 | 3 | 7 | 0 | 0.002705 | 0.000934 | 0.002705 | 0 | 0 |
| neutral_weighted_glucose | 7 | 7 | 3 | 3 | 7 | 0 | 0.008382 | 0.003402 | 0.008382 | 0 | 0 |
| static_weighted_glucose | 7 | 7 | 3 | 3 | 7 | 0 | 0.02886 | 0.0199 | 0.008158 | 0 | 0 |
| cached_trace_no_adapter_final | 7 | 7 | 3 | 3 | 7 | 7 | 0.038 | 0.02232 | 0.008158 | 0.007955 | 0 |
| event_adapter_final | 7 | 7 | 3 | 3 | 7 | 7 | 0.03797 | 0.02241 | 0.006671 | 0.007955 | 0.001455 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 14 | 14 | 14 | 0.007955 | 0.001186 | 0.0007273 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 7 | 7 | 1 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | 0.005676 |
| weighted_binary_input_delta_protocol_time | 0.005676 |
| static_weights_delta_final_cpu | -0.0002233 |
| static_weights_delta_protocol_time | 0.02048 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.009141 |
| adapter_delta_inference_delta_final_cpu | -0.001487 |
| adapter_delta_inference_delta_protocol_time | -3.248e-05 |
| adapter_inference_wall_time | 0.001455 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | medium | 0.001227 | 0.001227 | 0.001436 | 0.0209 | 0 | 0.003056 | -0.002008 | -0.0006544 | 0.001354 |
| non_symmetric_control | small | -0.00012 | -0.00012 | -0.000814 | 0.01502 | 0 | 0.004029 | 0.001278 | 0.002551 | 0.001273 |
| strong_symmetry | small | 0.003164 | 0.003164 | -0.001342 | 0.01275 | 0 | 0.001144 | -0.0005665 | 0.0007933 | 0.00136 |
| weak_symmetry | medium | 0.01554 | 0.01554 | -0.0004685 | 0.03053 | 0 | 0.02578 | -0.003268 | -0.001528 | 0.00174 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 1 | 1 | 1 | 0 | 0 | 0 | 0.03034 | 0.0446 | 0.04914 | -0.002606 | 4 | 2 | 1 | event_collection_overhead_only |
| php | php_p4_h3 | 1 | 1 | 1 | 0 | 0 | 0 | 0.002925 | 0.01255 | 0.001014 | -0.0003162 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 1 | 1 | 1 | 0 | 0 | 0 | 0.003402 | 0.01295 | 0.001275 | 0.001903 | 33 | 30 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | 1 | 1 | 1 | 0 | 0 | 0 | -0.00012 | 0.01502 | 0.004029 | 0.002551 | 9 | 0 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | 1 | 1 | 1 | 0 | 0 | 0 | -0.000945 | 0.02153 | 0.004609 | -0.0004545 | 14 | 13 | 1 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | 1 | 1 | 1 | 0 | 0 | 0 | 0.003398 | 0.02026 | 0.001502 | -0.0008544 | 10 | 0 | 1 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 1 | 1 | 1 | 0 | 0 | 0 | 0.000733 | 0.01647 | 0.002422 | -0.0004503 | 84 | 69 | 1 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | plain_unguided_glucose | 1 | 1 | 0.01355 | 0.01355 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 1 | 1 | 0.0439 | 0.0439 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 1 | 1 | 0.08849 | 0.04324 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 1 | 1 | 0.1376 | 0.04324 | 0.04684 | 1 |
| dominating_set_hex | event_adapter_final | 1 | 1 | 0.135 | 0.03845 | 0.04684 | 1 |
| php | plain_unguided_glucose | 2 | 2 | 0 | 0 | 0 | 0 |
| php | neutral_weighted_glucose | 2 | 2 | 0.003164 | 0.003164 | 0 | 0 |
| php | static_weighted_glucose | 2 | 2 | 0.01591 | 0.001821 | 0 | 0 |
| php | cached_trace_no_adapter_final | 2 | 2 | 0.01706 | 0.001821 | 0 | 2 |
| php | event_adapter_final | 2 | 2 | 0.01785 | 0.001255 | 0 | 2 |
| random_3sat_control | plain_unguided_glucose | 3 | 3 | 0.000893 | 0.000893 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 3 | 3 | 0.001671 | 0.001671 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 3 | 3 | 0.02061 | 0.002357 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 3 | 3 | 0.02399 | 0.002357 | 0.002365 | 3 |
| random_3sat_control | event_adapter_final | 3 | 3 | 0.0244 | 0.001444 | 0.002365 | 3 |
| subset_cardinality | plain_unguided_glucose | 1 | 1 | 0.002703 | 0.002703 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 1 | 1 | 0.003436 | 0.003436 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 1 | 1 | 0.0199 | 0.003152 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 1 | 1 | 0.02232 | 0.003152 | 0.001754 | 1 |
| subset_cardinality | event_adapter_final | 1 | 1 | 0.02187 | 0.001414 | 0.001754 | 1 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
