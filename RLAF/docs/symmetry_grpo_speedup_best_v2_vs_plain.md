# GRPO Best v2 vs Plain Glucose

Comparison: `event_adapter_final - plain_unguided_glucose` on the existing v2 runtime run.

This is a paired comparison against basic Glucose. `final_cpu_time` measures only the final solver call; `protocol_accounted_time` includes static inference, event warmup/collection, event attach, adapter inference, and final solve. Speedup claims should use `protocol_accounted_time`.

## Inputs

- per-instance input: `runs/analysis/symmetry_grpo_speedup_best_v2_per_instance.csv`
- repeat output: `runs/analysis/symmetry_grpo_speedup_best_v2_vs_plain.csv`
- base output: `runs/analysis/symmetry_grpo_speedup_best_v2_vs_plain_by_base.csv`
- family output: `runs/analysis/symmetry_grpo_speedup_best_v2_vs_plain_by_family.csv`
- overall output: `runs/analysis/symmetry_grpo_speedup_best_v2_vs_plain_overall.csv`

## Headline

- base instances: 35
- protocol-time speedup bases: 0/35
- final-CPU speedup bases: 2/35
- decision-reduction bases: 14/35
- conflict-reduction bases: 12/35
- known-label correctness rows: plain 279/279, adapter 279/279

Current interpretation: this run does not support an end-to-end speedup claim against basic Glucose because protocol-time deltas are not negative at base level. Search-count reductions are mechanism evidence only.

## Overall Base-Paired Summary

| metric | base_instances | base_mean_delta_adapter_minus_plain | base_median_delta_adapter_minus_plain | base_adapter_better | repeat_rows | row_adapter_better |
| --- | --- | --- | --- | --- | --- | --- |
| final_cpu_time | 35 | 0.129125 | 0.000800333 | 2 | 315 | 80 |
| protocol_accounted_time | 35 | 0.932582 | 0.0125475 | 0 | 315 | 0 |
| final_decisions | 35 | -7.6 | 0 | 14 | 315 | 129 |
| final_conflicts | 35 | -4.53333 | 0 | 12 | 315 | 93 |

## Family Summary

| family | bases | protocol_speedup_bases | final_cpu_speedup_bases | decisions_down_bases | conflicts_down_bases | mean_base_delta_protocol_accounted_time | mean_base_delta_final_cpu_time | mean_base_delta_final_decisions | mean_base_delta_final_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | 2 | 0 | 1 | 0 | 0 | 0.010033 | -0.000152444 | 0 | 0 |
| php | 2 | 0 | 0 | 0 | 0 | 0.0113179 | 0.000838611 | 0.5 | 0.333333 |
| php_exit_all | 2 | 0 | 0 | 2 | 0 | 0.0115945 | 0.000809278 | -0.833333 | 0 |
| subset_cardinality | 3 | 0 | 0 | 3 | 2 | 0.0119145 | 0.000488741 | -23 | -9.33333 |
| even_colouring | 3 | 0 | 0 | 1 | 0 | 0.012009 | 0.000524667 | 0.555556 | 0 |
| php_exit_single | 3 | 0 | 0 | 2 | 2 | 0.0122558 | 0.000877 | -9.22222 | -0.444444 |
| random_3sat_control | 7 | 0 | 1 | 5 | 5 | 0.012989 | 0.00102292 | -28.8095 | -23.0952 |
| complete_coloring | 2 | 0 | 0 | 1 | 1 | 0.0311244 | 0.000465444 | -1 | -0.166667 |
| vertex_cover_torus | 7 | 0 | 0 | 0 | 2 | 2.45122 | 0.120393 | 1.09524 | 0.190476 |
| dominating_set_hex | 4 | 0 | 0 | 0 | 0 | 3.78855 | 0.914971 | 6.41667 | 7.66667 |

## Notes

- The evidence unit is `base_instance_id`; permutation variants and repeats are summarized inside each base.
- Negative delta means the GRPO event adapter path is lower than plain Glucose.
- `protocol_accounted_time` is the primary runtime metric for speedup; `final_cpu_time`, decisions, and conflicts are diagnostic/mechanism metrics.
