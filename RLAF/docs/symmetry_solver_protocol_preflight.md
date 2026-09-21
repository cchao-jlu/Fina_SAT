# SAT Symmetry Solver Protocol Preflight

This is a protocol and accounting preflight for event-conditioned SAT symmetry guidance.
It is not a solver speedup claim. The purpose is to verify that the solver-level
pipeline can run while explicitly accounting for warmup rollout, event extraction/attach,
adapter inference, and the final solve.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_stress_manifest.csv`
- event-role rows: `57` distinct CNFs
- repeats: `3`
- solver seed base: `1`
- warmup seed base: `1`
- final seed base: `1`
- static-only rows included: `False`
- final CPU limit: `5.0` seconds
- warmup CPU limit: `5.0` seconds
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

- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv`
- phase accounting CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_phases.csv`
- family summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_by_family.csv`
- base-instance paired summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_by_base_instance.csv`
- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_attribution.csv`
- base-instance attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_attribution_by_base.csv`
- guided-loss diagnostics CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_solver_protocol_preflight_guided_loss_diagnostics.csv`

## Coverage

| family | instances | base_instances |
| --- | --- | --- |
| complete_coloring | 6 | 2 |
| dominating_set_hex | 9 | 3 |
| even_colouring | 3 | 1 |
| php | 6 | 2 |
| php_exit_all | 3 | 1 |
| php_exit_single | 6 | 2 |
| subset_cardinality | 3 | 1 |
| tseitin_complete | 6 | 2 |
| vertex_cover_torus | 15 | 5 |

## Overall Method Accounting

`known_expected_instances` excludes rows whose manifest `expected_result` is `UNKNOWN`;
`known_expected_match_instances` is the correctness count on the remaining SAT/UNSAT-labelled rows.

| method | rows | solved_instances | known_expected_instances | known_expected_match_instances | protocol_supported_instances | events_available_instances | mean_protocol_accounted_time | median_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plain_unguided_glucose | 171 | 171 | 144 | 144 | 171 | 0 | 0.4028 | 0.002213 | 0.4028 | 0 | 0 |
| neutral_weighted_glucose | 171 | 171 | 144 | 144 | 171 | 0 | 0.6408 | 0.002992 | 0.6408 | 0 | 0 |
| static_weighted_glucose | 171 | 171 | 144 | 144 | 171 | 0 | 0.8675 | 0.02033 | 0.6401 | 0 | 0 |
| cached_trace_no_adapter_final | 171 | 171 | 144 | 144 | 171 | 171 | 1.51 | 0.02302 | 0.6401 | 0.6414 | 0 |
| event_adapter_final | 171 | 171 | 144 | 144 | 171 | 171 | 1.511 | 0.02378 | 0.6401 | 0.6414 | 0.001316 |

## Event Accounting

| event_method_rows | events_available_rows | protocol_supported_rows | mean_warmup_cpu_time | mean_event_attach_wall_time | mean_adapter_inference_wall_time |
| --- | --- | --- | --- | --- | --- |
| 342 | 342 | 342 | 0.6414 | 0.0006701 | 0.0006579 |

## Attribution Modes

| primary_attribution | rows | base_instances | variants |
| --- | --- | --- | --- |
| event_collection_overhead_only | 171 | 19 | 3 |

## Base-Instance Attribution

| family | base_instance_id | repeats | variants | plain_solved_rows | neutral_lost_rows | static_lost_rows | adapter_lost_rows | event_overhead_mean | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows | primary_attribution_modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k4_color3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002892 | 0 | 0 | 0 | event_collection_overhead_only |
| complete_coloring | k5_color4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002889 | 32.33 | 28.67 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x5_s3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.0474 | 7.667 | 4 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_3x6_s4 | 3 | 3 | 9 | 0 | 0 | 0 | 1.143 | 12.67 | 7.667 | 9 | event_collection_overhead_only |
| dominating_set_hex | dominating_set_hex_4x5_s5 | 3 | 3 | 9 | 0 | 0 | 0 | 5.001 | 28 | 15 | 9 | event_collection_overhead_only |
| even_colouring | even_colouring_torus_4x5_split | 3 | 3 | 9 | 0 | 0 | 0 | 0.002424 | 22 | 0 | 9 | event_collection_overhead_only |
| php | php_p4_h3 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002197 | 0 | 0 | 0 | event_collection_overhead_only |
| php | php_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001921 | 28.67 | 28 | 9 | event_collection_overhead_only |
| php_exit_all | php_exit_all_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002308 | 13.33 | 0.3333 | 9 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p5_h4 | 3 | 3 | 9 | 0 | 0 | 0 | 0.001679 | 1 | 0 | 0 | event_collection_overhead_only |
| php_exit_single | php_exit_single_p6_h5 | 3 | 3 | 9 | 0 | 0 | 0 | 0.003299 | 5 | 0 | 9 | event_collection_overhead_only |
| subset_cardinality | subset_cardinality_bw8 | 3 | 3 | 9 | 0 | 0 | 0 | 0.002685 | 90.67 | 72.67 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_even | 3 | 3 | 9 | 0 | 0 | 0 | 0.002308 | 7 | 0 | 9 | event_collection_overhead_only |
| tseitin_complete | tseitin_k5_odd | 3 | 3 | 9 | 0 | 0 | 0 | 0.003029 | 63 | 64 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.01737 | 4 | 5 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.02233 | 6.667 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.323 | 6.333 | 7.333 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | 3 | 3 | 9 | 0 | 0 | 0 | 0.6125 | 12 | 12 | 9 | event_collection_overhead_only |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | 3 | 3 | 9 | 0 | 0 | 0 | 5.005 | 16.33 | 16.33 | 9 | event_collection_overhead_only |

## Guided Loss Diagnostics

_None._

## Family Breakdown

| family | method | rows | solved_instances | mean_protocol_accounted_time | mean_final_cpu_time | mean_warmup_cpu_time | events_available_instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | plain_unguided_glucose | 18 | 18 | 0.001075 | 0.001075 | 0 | 0 |
| complete_coloring | neutral_weighted_glucose | 18 | 18 | 0.001651 | 0.001651 | 0 | 0 |
| complete_coloring | static_weighted_glucose | 18 | 18 | 0.02415 | 0.002085 | 0 | 0 |
| complete_coloring | cached_trace_no_adapter_final | 18 | 18 | 0.02704 | 0.002085 | 0.002075 | 18 |
| complete_coloring | event_adapter_final | 18 | 18 | 0.02778 | 0.001087 | 0.002075 | 18 |
| dominating_set_hex | plain_unguided_glucose | 27 | 27 | 0.8369 | 0.8369 | 0 | 0 |
| dominating_set_hex | neutral_weighted_glucose | 27 | 27 | 2.061 | 2.061 | 0 | 0 |
| dominating_set_hex | static_weighted_glucose | 27 | 27 | 2.418 | 2.059 | 0 | 0 |
| dominating_set_hex | cached_trace_no_adapter_final | 27 | 27 | 4.482 | 2.059 | 2.063 | 27 |
| dominating_set_hex | event_adapter_final | 27 | 27 | 4.483 | 2.059 | 2.063 | 27 |
| even_colouring | plain_unguided_glucose | 9 | 9 | 0.001395 | 0.001395 | 0 | 0 |
| even_colouring | neutral_weighted_glucose | 9 | 9 | 0.001884 | 0.001884 | 0 | 0 |
| even_colouring | static_weighted_glucose | 9 | 9 | 0.02138 | 0.001632 | 0 | 0 |
| even_colouring | cached_trace_no_adapter_final | 9 | 9 | 0.0238 | 0.001632 | 0.001771 | 9 |
| even_colouring | event_adapter_final | 9 | 9 | 0.02539 | 0.001887 | 0.001771 | 9 |
| php | plain_unguided_glucose | 18 | 18 | 0.0008119 | 0.0008119 | 0 | 0 |
| php | neutral_weighted_glucose | 18 | 18 | 0.001329 | 0.001329 | 0 | 0 |
| php | static_weighted_glucose | 18 | 18 | 0.01421 | 0.001299 | 0 | 0 |
| php | cached_trace_no_adapter_final | 18 | 18 | 0.01627 | 0.001299 | 0.001458 | 18 |
| php | event_adapter_final | 18 | 18 | 0.01805 | 0.001821 | 0.001458 | 18 |
| php_exit_all | plain_unguided_glucose | 9 | 9 | 0.001414 | 0.001414 | 0 | 0 |
| php_exit_all | neutral_weighted_glucose | 9 | 9 | 0.00151 | 0.00151 | 0 | 0 |
| php_exit_all | static_weighted_glucose | 9 | 9 | 0.01657 | 0.00101 | 0 | 0 |
| php_exit_all | cached_trace_no_adapter_final | 9 | 9 | 0.01888 | 0.00101 | 0.00166 | 9 |
| php_exit_all | event_adapter_final | 9 | 9 | 0.02116 | 0.002021 | 0.00166 | 9 |
| php_exit_single | plain_unguided_glucose | 18 | 18 | 0.00131 | 0.00131 | 0 | 0 |
| php_exit_single | neutral_weighted_glucose | 18 | 18 | 0.002371 | 0.002371 | 0 | 0 |
| php_exit_single | static_weighted_glucose | 18 | 18 | 0.01841 | 0.002197 | 0 | 0 |
| php_exit_single | cached_trace_no_adapter_final | 18 | 18 | 0.0209 | 0.002197 | 0.001939 | 18 |
| php_exit_single | event_adapter_final | 18 | 18 | 0.02227 | 0.002298 | 0.001939 | 18 |
| subset_cardinality | plain_unguided_glucose | 9 | 9 | 0.001674 | 0.001674 | 0 | 0 |
| subset_cardinality | neutral_weighted_glucose | 9 | 9 | 0.00208 | 0.00208 | 0 | 0 |
| subset_cardinality | static_weighted_glucose | 9 | 9 | 0.01797 | 0.002109 | 0 | 0 |
| subset_cardinality | cached_trace_no_adapter_final | 9 | 9 | 0.02065 | 0.002109 | 0.00198 | 9 |
| subset_cardinality | event_adapter_final | 9 | 9 | 0.02095 | 0.001122 | 0.00198 | 9 |
| tseitin_complete | plain_unguided_glucose | 18 | 18 | 0.001433 | 0.001433 | 0 | 0 |
| tseitin_complete | neutral_weighted_glucose | 18 | 18 | 0.002151 | 0.002151 | 0 | 0 |
| tseitin_complete | static_weighted_glucose | 18 | 18 | 0.01362 | 0.001635 | 0 | 0 |
| tseitin_complete | cached_trace_no_adapter_final | 18 | 18 | 0.01629 | 0.001635 | 0.002044 | 18 |
| tseitin_complete | event_adapter_final | 18 | 18 | 0.01695 | 0.001076 | 0.002044 | 18 |
| vertex_cover_torus | plain_unguided_glucose | 45 | 45 | 1.026 | 1.026 | 0 | 0 |
| vertex_cover_torus | neutral_weighted_glucose | 45 | 45 | 1.194 | 1.194 | 0 | 0 |
| vertex_cover_torus | static_weighted_glucose | 45 | 45 | 1.806 | 1.193 | 0 | 0 |
| vertex_cover_torus | cached_trace_no_adapter_final | 45 | 45 | 3.002 | 1.193 | 1.195 | 45 |
| vertex_cover_torus | event_adapter_final | 45 | 45 | 3.004 | 1.193 | 1.195 | 45 |

## Interpretation

This run is a repeated paired runtime preflight and attribution ledger, not a
solver speedup claim. If the Glucose seed has no measurable effect on these
instances, interpret repeats as runtime stability rather than seed stability.
Any later runtime comparison should keep the neutral weighted baseline and the
cached-trace no-adapter ablation so the weighted path, static weights, event
collection overhead, and adapter delta remain separable.
