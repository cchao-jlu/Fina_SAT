# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_AdapterDelta_v2_Full/iter=235.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_canonical_order_harder_equiv_manifest.csv`
- event-role rows: `12` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `5`
- trace LBD threshold: `2`
- variants included: `base,perm_seed1730,perm_seed1731`
- permutation variants included: `True`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_wc5_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 2 | strong_symmetry | large | main | strong |
| php | 6 | 2 | strong_symmetry | large | main | strong |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 36 | 36 | 36 | 36 | 36 | 0 | 1.974 | 1.87 | 1.974 | 0 | 0 |
| neutral_weighted_glucose | 36 | 36 | 36 | 36 | 36 | 0 | 1.849 | 1.773 | 1.849 | 0 | 0 |
| static_weighted_glucose | 36 | 36 | 36 | 36 | 36 | 0 | 1.904 | 1.878 | 1.791 | 0 | 0 |
| cached_trace_no_adapter_final | 36 | 36 | 36 | 36 | 36 | 36 | 1.914 | 1.89 | 1.791 | 0.008937 | 0 |
| event_adapter_final | 36 | 36 | 36 | 36 | 36 | 36 | 1.944 | 1.892 | 1.818 | 0.008937 | 0.003398 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 72 | 72 | 72 | 0.008937 | 0.001005 | 0.001699 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 36 | 4 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.1255 |
| weighted_binary_input_delta_protocol_time | -0.1255 |
| static_weights_delta_final_cpu | -0.05822 |
| static_weights_delta_protocol_time | 0.0548 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.009942 |
| adapter_delta_inference_delta_final_cpu | 0.02689 |
| adapter_delta_inference_delta_protocol_time | 0.03029 |
| adapter_inference_wall_time | 0.003398 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strong_symmetry | large | -0.1255 | -0.1255 | -0.05822 | 0.0548 | 0 | 0.009942 | 0.02689 | 0.03029 | 0.003398 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2878 | 0.03445 | 0.01235 | 0.2348 | 11 | 5 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04895 | 0.1221 | 0.009212 | -0.1726 | 10 | 5 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2999 | 0.0156 | 0.0115 | 0.2362 | 11 | 5 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0366 | 0.04705 | 0.006705 | -0.1773 | 10 | 5 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 1.963 | 1.963 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 1.843 | 1.843 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 1.921 | 1.782 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 1.932 | 1.782 | 0.009611 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 1.963 | 1.81 | 0.009611 | 18 |
| php | plain_unguided_glucose | 18 | 18 | 1.986 | 1.986 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.855 | 1.855 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.886 | 1.799 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.895 | 1.799 | 0.008263 | 18 |
| php | event_adapter_final | 18 | 18 | 1.925 | 1.826 | 0.008263 | 18 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
