# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_3_WC1_Continuation/iter=15.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_runtime_v12_canonical_manifest.csv`
- event-role rows: `45` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `10.0` seconds
- warmup CPU limit: `5.0` seconds
- warmup conflict limit: `3`
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_guided_loss_diagnostics.csv`
- timeout/correctness CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/echosat_symmetry_grpo_v1_3_acceptance_iter=15_canonical_low_warmup_wc3_timeout_correctness.csv`

## Coverage

| family | instances | base_instances | control_types | scales | benchmark_roles | symmetry_strengths |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 9 | 3 | strong_symmetry | large | main | strong |
| php | 6 | 2 | strong_symmetry | large | main | strong |
| random_3sat_control | 21 | 7 | non_symmetric_control | large | control | none |
| subset_cardinality | 9 | 3 | weak_symmetry | large,medium | main | weak |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.306 | 0.4933 | 1.306 | 0 | 0 |
| neutral_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.132 | 0.4817 | 1.132 | 0 | 0 |
| static_weighted_glucose | 135 | 135 | 72 | 72 | 135 | 0 | 1.002 | 0.186 | 0.8852 | 0 | 0 |
| cached_trace_no_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.009 | 0.1899 | 0.8852 | 0.005836 | 0 |
| event_adapter_final | 135 | 135 | 72 | 72 | 135 | 135 | 1.027 | 0.298 | 0.9 | 0.005836 | 0.003612 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 270 | 270 | 270 | 0.005836 | 0.000878 | 0.001806 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 135 | 15 | 3 |

## Fixed Attribution Matrix

The runtime v1 deltas are paired within `(repeat_id, base_instance_id, variant, instance_id)`:

- `weighted_binary_input_delta = neutral_weighted_glucose - plain_unguided_glucose`
- `static_weights_delta = static_weighted_glucose - neutral_weighted_glucose`
- `event_collection_overhead_delta = cached_trace_no_adapter_final - static_weighted_glucose`
- `adapter_delta_inference_delta = event_adapter_final - cached_trace_no_adapter_final`

| attribution_delta | mean_delta |
| --- | --- |
| weighted_binary_input_delta_final_cpu | -0.1745 |
| weighted_binary_input_delta_protocol_time | -0.1745 |
| static_weights_delta_final_cpu | -0.2466 |
| static_weights_delta_protocol_time | -0.1299 |
| event_collection_overhead_delta_final_cpu | 0 |
| event_collection_overhead_delta_protocol_time | 0.006714 |
| adapter_delta_inference_delta_final_cpu | 0.0148 |
| adapter_delta_inference_delta_protocol_time | 0.01841 |
| adapter_inference_wall_time | 0.003612 |

## Attribution Matrix By Stratum

| control_type | scale | weighted_binary_input_delta_final_cpu | weighted_binary_input_delta_protocol_time | static_weights_delta_final_cpu | static_weights_delta_protocol_time | event_collection_overhead_delta_final_cpu | event_collection_overhead_delta_protocol_time | adapter_delta_inference_delta_final_cpu | adapter_delta_inference_delta_protocol_time | adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | large | -0.3087 | -0.3087 | -0.4914 | -0.3484 | 0 | 0.007331 | 0.1301 | 0.1342 | 0.004099 |
| strong_symmetry | large | -0.09116 | -0.09116 | -0.05216 | 0.06028 | 0 | 0.008627 | -0.138 | -0.1343 | 0.003661 |
| weak_symmetry | large | -0.0005239 | -0.0005239 | 0.0008951 | 0.07703 | 0 | 0.0022 | 0.0005767 | 0.003042 | 0.002465 |
| weak_symmetry | medium | 0.0003608 | 0.0003608 | 7.889e-05 | 0.035 | 0 | 0.001858 | 0.0001566 | 0.002408 | 0.002251 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | weighted_binary_input_delta_protocol_time_mean | static_weights_delta_protocol_time_mean | event_collection_overhead_delta_protocol_time_mean | adapter_delta_inference_delta_protocol_time_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.2606 | -0.009484 | 0.01058 | -0.2014 | 9 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k8_color7 | 3 | 3 | 9 | 0 | 0 | 0 | 0.00438 | 0.1086 | 0.006981 | -0.006946 | 7 | 3 | 9 | event_collection_overhead_only |
| complete_coloring | k9_color8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04716 | 0.09733 | 0.00883 | -0.1444 | 8.667 | 3 | 9 | event_collection_overhead_only |
| php | php_p10_h9 | 3 | 3 | 9 | 0 | 0 | 0 | -0.287 | 0.00113 | 0.01004 | -0.1796 | 9 | 3 | 9 | event_collection_overhead_only |
| php | php_p9_h8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.04025 | 0.1039 | 0.006698 | -0.1393 | 8.667 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001903 | 0.1141 | 0.007326 | 0.00431 | 22 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | 3 | 3 | 9 | 0 | 0 | 0 | -0.4312 | 0.05769 | 0.005603 | 0.1422 | 28 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | 3 | 3 | 9 | 0 | 0 | 0 | -0.3153 | -0.1151 | 0.005093 | 0.008231 | 39 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | 3 | 3 | 9 | 0 | 0 | 0 | 0.09 | -0.1126 | 0.008634 | 0.2147 | 26 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 3 | 3 | 9 | 0 | 0 | 0 | -2.498 | -0.9412 | 0.008264 | -0.3219 | 35 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 3 | 3 | 9 | 0 | 0 | 0 | 0.6895 | -0.3327 | 0.007861 | 0.8653 | 34 | 3 | 9 | event_collection_overhead_only |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 3 | 3 | 9 | 0 | 0 | 0 | 0.3024 | -1.109 | 0.008533 | 0.02632 | 48 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw10 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0004476 | 0.09745 | 0.00248 | 0.003459 | 8.333 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw12 | 3 | 3 | 9 | 0 | 0 | 0 | -0.0006002 | 0.0566 | 0.001919 | 0.002624 | 10.67 | 3 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0003608 | 0.035 | 0.001858 | 0.002408 | 13.33 | 3 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 27 | 27 | 1.325 | 1.325 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 27 | 27 | 1.255 | 1.255 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 27 | 27 | 1.321 | 1.21 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 27 | 27 | 1.329 | 1.21 | 0.007812 | 27 |
| complete_coloring | event_adapter_final | 27 | 27 | 1.212 | 1.089 | 0.007812 | 27 |
| php | plain_unguided_glucose | 18 | 18 | 1.972 | 1.972 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 1.849 | 1.849 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 1.901 | 1.785 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 1.909 | 1.785 | 0.007559 | 18 |
| php | event_adapter_final | 18 | 18 | 1.75 | 1.623 | 0.007559 | 18 |
| random_3sat_control | plain_unguided_glucose | 63 | 63 | 1.667 | 1.667 | 0 | 0 |
| random_3sat_control | neutral_weighted_glucose | 63 | 63 | 1.358 | 1.358 | 0 | 0 |
| random_3sat_control | static_weighted_glucose | 63 | 63 | 1.01 | 0.867 | 0 | 0 |
| random_3sat_control | cached_trace_no_adapter_final | 63 | 63 | 1.017 | 0.867 | 0.006422 | 63 |
| random_3sat_control | event_adapter_final | 63 | 63 | 1.152 | 0.997 | 0.006422 | 63 |
| subset_cardinality | plain_unguided_glucose | 27 | 27 | 0.00191 | 0.00191 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 27 | 27 | 0.001681 | 0.001681 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 27 | 27 | 0.0647 | 0.002304 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 27 | 27 | 0.06679 | 0.002304 | 0.001343 | 27 |
| subset_cardinality | event_adapter_final | 27 | 27 | 0.06962 | 0.002741 | 0.001343 | 27 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
