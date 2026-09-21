# SAT Symmetry Runtime-Positive Subset v2

This is an offline diagnostic report. It asks whether the event adapter changed
the final solver search on the v2 runtime protocol. It is not a solver speedup
claim, and it does not train a model, run a gate/selector, or rerun any solver.

## Inputs

- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv`
- per-instance CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv`
- primary comparison: `event_adapter_final - cached_trace_no_adapter_final`
- secondary comparison: `event_adapter_final - static_weighted_glucose`
- unit of analysis: `base_instance_id`; `variant x repeat_id` are observations inside each base
- CPU direction epsilon: `1e-06` seconds
- decision/conflict epsilon: `0.0`
- W05 orbit overlap source: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_patched_pretrue_w05_cached_adapter_orbits.csv`

## Classification Rules

Deltas are `adapter - baseline`, so negative deltas mean the adapter used less
final CPU, fewer decisions, or fewer conflicts than the baseline.

- `strict_positive`: final CPU is down for a majority of observations, and decisions or conflicts are also down for a majority, with no majority search worsening.
- `timing_only_positive`: final CPU is down for a majority, but decisions/conflicts have no stable direction.
- `no_effect`: neither timing nor search has a stable majority direction.
- `negative`: final CPU, decisions, or conflicts increase for a majority.

## Runtime Viability Mining

| primary_classification | base_instances |
| --- | --- |
| strict_positive | 2 |
| timing_only_positive | 6 |
| no_effect | 1 |
| negative | 26 |

### By Family

| family | primary_classification | base_instances |
| --- | --- | --- |
| complete_coloring | negative | 1 |
| complete_coloring | strict_positive | 1 |
| dominating_set_hex | negative | 3 |
| dominating_set_hex | timing_only_positive | 1 |
| even_colouring | timing_only_positive | 3 |
| php | negative | 1 |
| php | timing_only_positive | 1 |
| php_exit_all | negative | 1 |
| php_exit_all | timing_only_positive | 1 |
| php_exit_single | negative | 3 |
| random_3sat_control | negative | 6 |
| random_3sat_control | strict_positive | 1 |
| subset_cardinality | negative | 3 |
| tseitin_complete | negative | 1 |
| tseitin_complete | no_effect | 1 |
| vertex_cover_torus | negative | 7 |

### Strict Positives

| family | base_instance_id | control_type | scale | primary_classification | primary_final_cpu_down_count | primary_final_cpu_up_count | primary_final_cpu_mean_delta | primary_final_decisions_down_count | primary_final_decisions_up_count | primary_final_decisions_mean_delta | primary_final_conflicts_down_count | primary_final_conflicts_up_count | primary_final_conflicts_mean_delta | event_state_l2_sum_mean | event_adapter_graph_gate_evidence_mean | warmup_decisions_mean | warmup_conflicts_mean | secondary_protocol_overhead_swallows_final_cpu_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | non_symmetric_control | large | strict_positive | 7 | 2 | -0.0007133 | 3 | 0 | -0.6667 | 9 | 0 | -5 | 162.9 | 1.609 | 19 | 6 | True |
| complete_coloring | k5_color4 | strong_symmetry | small | strict_positive | 5 | 4 | -0.0004462 | 6 | 3 | -2 | 6 | 3 | -0.6667 | 174.9 | 3.192 | 32.33 | 28.67 | True |

The table above is the mechanical strict-positive bucket. The priority deep dive
below stays focused on the three pre-identified candidates; other strict-like rows
are weaker evidence because they are controls, very small timing effects, or
variant-mixed search changes.

Initial strict candidates requested for first inspection:

- `dominating_set_hex_3x6_s4`: `negative`; CPU down `3/9`, decisions down `6/9`, conflicts down `9/9`; mean final CPU delta `0.007801`, decisions delta `-1`, conflicts delta `-2.667`.
- `random_3sat_control_v20_c85_seed1901`: `negative`; CPU down `4/9`, decisions down `9/9`, conflicts down `0/9`; mean final CPU delta `-8.556e-05`, decisions delta `-2`, conflicts delta `0`.
- `subset_cardinality_bw12`: `negative`; CPU down `2/9`, decisions down `6/9`, conflicts down `6/9`; mean final CPU delta `0.001179`, decisions delta `-28.33`, conflicts delta `-14`.

### Timing-Only Positives

| family | base_instance_id | control_type | scale | primary_classification | primary_final_cpu_down_count | primary_final_cpu_up_count | primary_final_cpu_mean_delta | primary_final_decisions_down_count | primary_final_decisions_up_count | primary_final_decisions_mean_delta | primary_final_conflicts_down_count | primary_final_conflicts_up_count | primary_final_conflicts_mean_delta | event_state_l2_sum_mean | event_adapter_graph_gate_evidence_mean | warmup_decisions_mean | warmup_conflicts_mean | secondary_protocol_overhead_swallows_final_cpu_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | weak_symmetry | medium | timing_only_positive | 8 | 1 | -0.007115 | 3 | 3 | -1 | 3 | 0 | -0.3333 | 47.63 | 1.465 | 7.667 | 4 | True |
| even_colouring | even_colouring_torus_5x5_split | weak_symmetry | large | timing_only_positive | 7 | 2 | -0.001151 | 0 | 0 | 0 | 0 | 0 | 0 | 85.57 | 0.6931 | 28 | 0 | True |
| php | php_p4_h3 | strong_symmetry | small | timing_only_positive | 7 | 2 | -0.000539 | 0 | 0 | 0 | 0 | 0 | 0 | 13.75 | 0 | 0 | 0 | True |
| even_colouring | even_colouring_torus_4x6_split | weak_symmetry | large | timing_only_positive | 6 | 3 | -0.0007619 | 0 | 0 | 0 | 0 | 0 | 0 | 82.2 | 0.6931 | 27 | 0 | True |
| php_exit_all | php_exit_all_p6_h5 | weak_symmetry | medium | timing_only_positive | 6 | 3 | -0.0006279 | 0 | 0 | 0 | 0 | 0 | 0 | 58.56 | 0.6931 | 6 | 0 | True |
| even_colouring | even_colouring_torus_4x5_split | weak_symmetry | large | timing_only_positive | 5 | 4 | -5.889e-05 | 0 | 0 | 0 | 0 | 0 | 0 | 68.77 | 0.6931 | 22 | 0 | True |

### No-Effect Bases

| family | base_instance_id | control_type | scale | primary_classification | primary_final_cpu_down_count | primary_final_cpu_up_count | primary_final_cpu_mean_delta | primary_final_decisions_down_count | primary_final_decisions_up_count | primary_final_decisions_mean_delta | primary_final_conflicts_down_count | primary_final_conflicts_up_count | primary_final_conflicts_mean_delta | event_state_l2_sum_mean | event_adapter_graph_gate_evidence_mean | warmup_decisions_mean | warmup_conflicts_mean | secondary_protocol_overhead_swallows_final_cpu_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tseitin_complete | tseitin_k5_odd | strong_symmetry | small | no_effect | 4 | 4 | -0.0002976 | 0 | 0 | 0 | 0 | 0 | 0 | 217.6 | 4.154 | 63 | 64 | True |

### Negative / Search-Worsening Bases

| family | base_instance_id | control_type | scale | primary_classification | primary_final_cpu_down_count | primary_final_cpu_up_count | primary_final_cpu_mean_delta | primary_final_decisions_down_count | primary_final_decisions_up_count | primary_final_decisions_mean_delta | primary_final_conflicts_down_count | primary_final_conflicts_up_count | primary_final_conflicts_mean_delta | event_state_l2_sum_mean | event_adapter_graph_gate_evidence_mean | warmup_decisions_mean | warmup_conflicts_mean | secondary_protocol_overhead_swallows_final_cpu_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality | subset_cardinality_bw10 | weak_symmetry | large | negative | 7 | 2 | -0.000408 | 0 | 9 | 25.33 | 3 | 6 | 4.667 | 1463 | 4.197 | 167.7 | 143 | True |
| dominating_set_hex | dominating_set_hex_4x6_s6 | weak_symmetry | stress | negative | 7 | 2 | -0.006382 | 0 | 6 | 9 | 0 | 6 | 10.67 | 189.4 | 2.696 | 32.33 | 16.67 | True |
| random_3sat_control | random_3sat_control_v40_c170_seed1903 | non_symmetric_control | medium | negative | 6 | 3 | -0.0007192 | 3 | 6 | 0.3333 | 0 | 9 | 1 | 68.47 | 0.6931 | 10 | 0 | True |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | strong_symmetry | medium | negative | 6 | 3 | -0.003013 | 0 | 6 | 1 | 0 | 0 | 0 | 41.89 | 1.609 | 4 | 5 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | strong_symmetry | stress | negative | 5 | 4 | 0.001986 | 3 | 6 | 1 | 6 | 3 | -0.3333 | 176.2 | 3.028 | 23.33 | 24 | False |
| random_3sat_control | random_3sat_control_v35_c149_seed1911 | non_symmetric_control | medium | negative | 5 | 3 | -0.0006966 | 0 | 9 | 2 | 0 | 9 | 2 | 155 | 1.792 | 14 | 7 | True |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | non_symmetric_control | small | negative | 4 | 5 | -8.556e-05 | 9 | 0 | -2 | 0 | 0 | 0 | 33.84 | 0.6931 | 9 | 0 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | weak_symmetry | large | negative | 4 | 5 | 0.0007689 | 6 | 3 | 0 | 6 | 3 | -1.333 | 157.9 | 2.723 | 28 | 15 | False |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | strong_symmetry | stress | negative | 4 | 5 | 0.0007844 | 3 | 3 | 0.6667 | 3 | 3 | 0.6667 | 131.4 | 2.685 | 16.33 | 16.33 | False |
| random_3sat_control | random_3sat_control_v80_c340_seed1913 | non_symmetric_control | large | negative | 4 | 5 | -0.0004704 | 0 | 9 | 4 | 0 | 9 | 9.333 | 171.6 | 1.099 | 23 | 2 | True |
| php_exit_single | php_exit_single_p7_h6 | weak_symmetry | large | negative | 4 | 5 | -0.0003438 | 0 | 0 | 0 | 0 | 0 | 0 | 67.72 | 0.6931 | 6 | 0 | True |
| random_3sat_control | random_3sat_control_v100_c600_seed1914 | non_symmetric_control | large | negative | 4 | 5 | -0.000322 | 0 | 9 | 40.67 | 0 | 9 | 39 | 4624 | 4.502 | 180.3 | 158.3 | True |
| complete_coloring | k4_color3 | strong_symmetry | small | negative | 4 | 5 | -0.0002941 | 0 | 0 | 0 | 0 | 0 | 0 | 13.75 | 0 | 0 | 0 | True |
| php_exit_single | php_exit_single_p5_h4 | weak_symmetry | medium | negative | 4 | 5 | 0.000179 | 0 | 0 | 0 | 0 | 0 | 0 | 23.19 | 0 | 1 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | strong_symmetry | large | negative | 4 | 5 | 0.0003622 | 0 | 6 | 1.667 | 0 | 6 | 0.6667 | 100.2 | 2.267 | 10 | 11 | False |
| php_exit_all | php_exit_all_p5_h4 | weak_symmetry | medium | negative | 3 | 6 | 0.0008909 | 9 | 0 | -1 | 0 | 0 | 0 | 44.36 | 0.6931 | 13.33 | 0.3333 | False |
| dominating_set_hex | dominating_set_hex_3x6_s4 | weak_symmetry | large | negative | 3 | 6 | 0.007801 | 6 | 3 | -1 | 9 | 0 | -2.667 | 76.06 | 2.149 | 12.67 | 7.667 | False |
| php | php_p5_h4 | strong_symmetry | small | negative | 3 | 5 | 8.744e-05 | 3 | 6 | 2.333 | 3 | 6 | 0 | 171.4 | 3.15 | 28.67 | 28 | False |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | strong_symmetry | large | negative | 3 | 6 | 0.001147 | 0 | 3 | 0.3333 | 3 | 0 | -0.3333 | 65.1 | 1.99 | 6.333 | 7.333 | False |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | strong_symmetry | large | negative | 3 | 6 | 0.0001326 | 0 | 9 | 1.333 | 0 | 3 | 0.3333 | 86.39 | 2.366 | 12 | 12 | False |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | strong_symmetry | medium | negative | 3 | 6 | 0.0006141 | 0 | 0 | 0 | 0 | 3 | 0.3333 | 54.13 | 1.946 | 6.667 | 7.333 | False |
| tseitin_complete | tseitin_k5_even | strong_symmetry | small | negative | 3 | 6 | 0.0008433 | 0 | 0 | 0 | 0 | 0 | 0 | 16.08 | 0.6931 | 7 | 0 | False |
| subset_cardinality | subset_cardinality_bw8 | weak_symmetry | medium | negative | 2 | 7 | 0.0006853 | 3 | 6 | -2.333 | 9 | 0 | -5.333 | 650.6 | 3.584 | 90.67 | 72.67 | False |
| subset_cardinality | subset_cardinality_bw12 | weak_symmetry | large | negative | 2 | 7 | 0.001179 | 6 | 3 | -28.33 | 6 | 3 | -14 | 3386 | 4.754 | 360.3 | 296.3 | False |
| random_3sat_control | random_3sat_control_v30_c128_seed1902 | non_symmetric_control | medium | negative | 1 | 7 | 0.0006754 | 3 | 3 | -0.6667 | 3 | 6 | 0.6667 | 164 | 2.345 | 15.33 | 14.33 | False |
| php_exit_single | php_exit_single_p6_h5 | weak_symmetry | medium | negative | 0 | 9 | 0.001287 | 0 | 0 | 0 | 0 | 0 | 0 | 48.2 | 0.6931 | 5 | 0 | False |

## Evidence Correlation

Layer 1 uses only repeat-level fields already present in the v2 attribution table.
Positive target values mean improvement because they are `-delta`.

### Evidence By Classification

| primary_classification | base_instances | named_initial_strict_candidates | event_state_l2_sum_mean_mean | event_state_l2_sum_mean_median | event_state_nonzero_vars_mean_mean | event_state_nonzero_vars_mean_median | event_adapter_graph_gate_evidence_mean_mean | event_adapter_graph_gate_evidence_mean_median | warmup_decisions_mean_mean | warmup_decisions_mean_median | warmup_conflicts_mean_mean | warmup_conflicts_mean_median | primary_final_cpu_mean_delta_mean | primary_final_cpu_mean_delta_median | primary_final_decisions_mean_delta_mean | primary_final_decisions_mean_delta_median | primary_final_conflicts_mean_delta_mean | primary_final_conflicts_mean_delta_median | secondary_protocol_time_mean_delta_mean | secondary_protocol_time_mean_delta_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| negative | 26 | 3 | 468.5 | 93.31 | 29.46 | 20.5 | 2.04 | 2.069 | 41.65 | 13 | 32.47 | 7.5 | 0.0002573 | 0.0002706 | 2.09 | 0.1667 | 1.744 | 0 | 1.047 | 0.004818 |
| no_effect | 1 | 0 | 217.6 | 217.6 | 10 | 10 | 4.154 | 4.154 | 63 | 63 | 64 | 64 | -0.0002976 | -0.0002976 | 0 | 0 | 0 | 0 | 0.002767 | 0.002767 |
| strict_positive | 2 | 0 | 168.9 | 168.9 | 40 | 40 | 2.401 | 2.401 | 25.67 | 25.67 | 17.33 | 17.33 | -0.0005798 | -0.0005798 | -1.333 | -1.333 | -2.833 | -2.833 | 0.0032 | 0.0032 |
| timing_only_positive | 6 | 0 | 59.41 | 63.67 | 34 | 38.5 | 0.7062 | 0.6931 | 15.11 | 14.83 | 0.6667 | 0 | -0.001709 | -0.0006949 | -0.1667 | 0 | -0.05556 | 0 | 0.009883 | 0.00372 |

### Top Correlations

| unit | evidence | target | n | pearson | spearman |
| --- | --- | --- | --- | --- | --- |
| base_instance | warmup_conflicts | primary_improvement_final_cpu | 35 | -0.08546 | -0.2492 |
| base_instance | warmup_conflicts | secondary_improvement_final_cpu | 35 | -0.08546 | -0.2492 |
| base_instance | event_state_nonzero_vars | primary_improvement_final_cpu | 35 | 0.04091 | 0.2419 |
| base_instance | event_state_nonzero_vars | secondary_improvement_final_cpu | 35 | 0.04091 | 0.2419 |
| base_instance | event_state_l2_sum | primary_improvement_final_decisions | 35 | -0.3574 | -0.2389 |
| base_instance | event_state_l2_sum | secondary_improvement_final_decisions | 35 | -0.3574 | -0.2389 |
| base_instance | event_adapter_graph_gate_evidence | primary_improvement_final_cpu | 35 | -0.08872 | -0.2272 |
| base_instance | event_adapter_graph_gate_evidence | secondary_improvement_final_cpu | 35 | -0.08872 | -0.2272 |
| base_instance | event_adapter_graph_gate_evidence | primary_improvement_final_decisions | 35 | -0.2033 | -0.1839 |
| base_instance | event_adapter_graph_gate_evidence | secondary_improvement_final_decisions | 35 | -0.2033 | -0.1839 |
| base_instance | event_state_nonzero_vars | primary_improvement_final_conflicts | 35 | -0.538 | -0.1707 |
| base_instance | event_state_nonzero_vars | secondary_improvement_final_conflicts | 35 | -0.538 | -0.1707 |
| base_instance | warmup_conflicts | primary_improvement_final_decisions | 35 | -0.01824 | -0.1692 |
| base_instance | warmup_conflicts | secondary_improvement_final_decisions | 35 | -0.01824 | -0.1692 |
| base_instance | event_state_l2_sum | primary_improvement_final_conflicts | 35 | -0.5049 | -0.08949 |
| base_instance | event_state_l2_sum | secondary_improvement_final_conflicts | 35 | -0.5049 | -0.08949 |
| base_instance | warmup_decisions | primary_improvement_final_decisions | 35 | 0.01272 | -0.08073 |
| base_instance | warmup_decisions | secondary_improvement_final_decisions | 35 | 0.01272 | -0.08073 |
| base_instance | event_state_nonzero_vars | primary_improvement_final_decisions | 35 | -0.4057 | -0.0728 |
| base_instance | event_state_nonzero_vars | secondary_improvement_final_decisions | 35 | -0.4057 | -0.0728 |
| base_instance | event_adapter_graph_gate_open_int | primary_improvement_final_decisions | 35 | -0.04668 | -0.06228 |
| base_instance | event_adapter_graph_gate_open_int | secondary_improvement_final_decisions | 35 | -0.04668 | -0.06228 |
| base_instance | event_adapter_graph_gate_open_int | primary_improvement_final_cpu | 35 | -0.01012 | -0.05053 |
| base_instance | event_adapter_graph_gate_open_int | secondary_improvement_final_cpu | 35 | -0.01012 | -0.05053 |
| base_instance | event_adapter_graph_gate_evidence | primary_improvement_final_conflicts | 35 | -0.181 | 0.03221 |
| base_instance | event_adapter_graph_gate_evidence | secondary_improvement_final_conflicts | 35 | -0.181 | 0.03221 |
| base_instance | event_adapter_graph_gate_open_int | primary_improvement_final_conflicts | 35 | -0.04592 | -0.0316 |
| base_instance | event_adapter_graph_gate_open_int | secondary_improvement_final_conflicts | 35 | -0.04592 | -0.0316 |
| base_instance | warmup_conflicts | primary_improvement_final_conflicts | 35 | -0.0899 | 0.02794 |
| base_instance | warmup_conflicts | secondary_improvement_final_conflicts | 35 | -0.0899 | 0.02794 |
| base_instance | event_state_l2_sum | primary_improvement_final_cpu | 35 | -0.04564 | -0.02241 |
| base_instance | event_state_l2_sum | secondary_improvement_final_cpu | 35 | -0.04564 | -0.02241 |
| base_instance | warmup_decisions | primary_improvement_final_cpu | 35 | -0.06847 | 0.008406 |
| base_instance | warmup_decisions | secondary_improvement_final_cpu | 35 | -0.06847 | 0.008406 |
| base_instance | warmup_decisions | primary_improvement_final_conflicts | 35 | -0.07078 | 0.004673 |
| base_instance | warmup_decisions | secondary_improvement_final_conflicts | 35 | -0.07078 | 0.004673 |
| ... truncated ... | 36 more rows | | | | |

## Candidate Deep Dive

The primary comparison shares the same warmup/event collection between cached trace
and adapter final solves. Therefore warmup can explain secondary protocol overhead
relative to `static_weighted_glucose`, but not the primary final-search deltas below.

### Variant Summary

| family | base_instance_id | variant | repeat_rows | primary_final_cpu_down_count | primary_final_cpu_up_count | primary_final_cpu_mean_delta | primary_final_decisions_down_count | primary_final_decisions_up_count | primary_final_decisions_mean_delta | primary_final_conflicts_down_count | primary_final_conflicts_up_count | primary_final_conflicts_mean_delta | event_state_l2_sum | event_adapter_graph_gate_open_rows | event_adapter_graph_gate_evidence | warmup_decisions | warmup_conflicts | secondary_protocol_time_mean_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 3 | 1 | 2 | 0.01566 | 3 | 0 | -1 | 3 | 0 | -2 | 63.71 | 3 | 1.946 | 10 | 6 | 1.133 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 3 | 2 | 1 | -0.01113 | 0 | 3 | 2 | 3 | 0 | -2 | 78.41 | 3 | 2.197 | 12 | 8 | 1.145 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 3 | 0 | 3 | 0.01887 | 3 | 0 | -4 | 3 | 0 | -4 | 86.05 | 3 | 2.303 | 16 | 9 | 1.163 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | base | 3 | 1 | 2 | -0.000591 | 3 | 0 | -2 | 0 | 0 | 0 | 33.86 | 3 | 0.6931 | 9 | 0 | 0.00244 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1730 | 3 | 1 | 2 | 0.0004077 | 3 | 0 | -2 | 0 | 0 | 0 | 33.84 | 3 | 0.6931 | 9 | 0 | 0.003497 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1731 | 3 | 2 | 1 | -7.333e-05 | 3 | 0 | -2 | 0 | 0 | 0 | 33.83 | 3 | 0.6931 | 9 | 0 | 0.003836 |
| subset_cardinality | subset_cardinality_bw12 | base | 3 | 2 | 1 | -0.000621 | 3 | 0 | -55 | 3 | 0 | -22 | 3623 | 3 | 4.804 | 384 | 312 | 0.002941 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 3 | 0 | 3 | 0.001565 | 0 | 3 | 13 | 0 | 3 | 1 | 3254 | 3 | 4.796 | 341 | 292 | 0.007948 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 3 | 0 | 3 | 0.002592 | 3 | 0 | -43 | 3 | 0 | -21 | 3282 | 3 | 4.663 | 356 | 285 | 0.007009 |

### Variant x Repeat Rows

| family | base_instance_id | variant | repeat_id | primary_delta_final_cpu | primary_delta_final_decisions | primary_delta_final_conflicts | primary_delta_protocol_time | event_state_l2_sum | event_state_nonzero_vars | event_adapter_graph_gate_open | event_adapter_graph_gate_evidence | warmup_decisions | warmup_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 0 | -0.01088 | -1 | -2 | -0.009687 | 63.71 | 18 | True | 1.946 | 10 | 6 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 1 | 0.00153 | -1 | -2 | 0.002715 | 63.71 | 18 | True | 1.946 | 10 | 6 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 2 | 0.05632 | -1 | -2 | 0.05755 | 63.71 | 18 | True | 1.946 | 10 | 6 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 0 | -0.01581 | 2 | -2 | -0.01463 | 78.41 | 18 | True | 2.197 | 12 | 8 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 1 | -0.02547 | 2 | -2 | -0.02428 | 78.41 | 18 | True | 2.197 | 12 | 8 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 2 | 0.0079 | 2 | -2 | 0.009096 | 78.41 | 18 | True | 2.197 | 12 | 8 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 0 | 0.02613 | -4 | -4 | 0.02733 | 86.05 | 18 | True | 2.303 | 16 | 9 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 1 | 0.02047 | -4 | -4 | 0.02177 | 86.05 | 18 | True | 2.303 | 16 | 9 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 2 | 0.01002 | -4 | -4 | 0.01122 | 86.05 | 18 | True | 2.303 | 16 | 9 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | base | 0 | -0.002855 | -2 | 0 | -0.001665 | 33.86 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | base | 1 | 0.000139 | -2 | 0 | 0.001342 | 33.86 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | base | 2 | 0.000943 | -2 | 0 | 0.002165 | 33.86 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1730 | 0 | 0.000704 | -2 | 0 | 0.0019 | 33.84 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1730 | 1 | -0.002369 | -2 | 0 | -0.00118 | 33.84 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1730 | 2 | 0.002888 | -2 | 0 | 0.004076 | 33.84 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1731 | 0 | -0.00035 | -2 | 0 | 0.0008361 | 33.83 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1731 | 1 | -6.9e-05 | -2 | 0 | 0.001116 | 33.83 | 20 | True | 0.6931 | 9 | 0 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1731 | 2 | 0.000199 | -2 | 0 | 0.00138 | 33.83 | 20 | True | 0.6931 | 9 | 0 |
| subset_cardinality | subset_cardinality_bw12 | base | 0 | 0.000296 | -55 | -22 | 0.001531 | 3623 | 49 | True | 4.804 | 384 | 312 |
| subset_cardinality | subset_cardinality_bw12 | base | 1 | -0.000171 | -55 | -22 | 0.001054 | 3623 | 49 | True | 4.804 | 384 | 312 |
| subset_cardinality | subset_cardinality_bw12 | base | 2 | -0.001988 | -55 | -22 | -0.0007024 | 3623 | 49 | True | 4.804 | 384 | 312 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | 0.001036 | 13 | 1 | 0.002267 | 3254 | 49 | True | 4.796 | 341 | 292 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | 0.001761 | 13 | 1 | 0.003273 | 3254 | 49 | True | 4.796 | 341 | 292 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | 0.001898 | 13 | 1 | 0.003152 | 3254 | 49 | True | 4.796 | 341 | 292 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 0 | 0.003494 | -43 | -21 | 0.004737 | 3282 | 49 | True | 4.663 | 356 | 285 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 1 | 0.001964 | -43 | -21 | 0.003243 | 3282 | 49 | True | 4.663 | 356 | 285 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 2 | 0.002317 | -43 | -21 | 0.003683 | 3282 | 49 | True | 4.663 | 356 | 285 |

Interpretation for the named strict candidates:

- `dominating_set_hex_3x6_s4`: adapter changed search on the final solve; conflicts drop in every variant/repeat, while final CPU mostly drops. Event gate is open on all rows. Protocol time still loses relative to static because event collection is much larger than the local final-solve gain.
- `subset_cardinality_bw12`: adapter changed search on two of three variants; the `perm_seed1730` variant has worse decisions/conflicts, so the evidence is strict by majority but not variant-uniform. Event evidence is strong, and protocol overhead still dominates.
- `random_3sat_control_v20_c85_seed1901`: decisions drop in every row, but conflicts are flat and CPU changes are tiny. Because this is a non-symmetric control, it is evidence that the adapter can perturb search, not evidence of symmetry-specific benefit.

## Orbit Overlap

Layer 2 joins existing W05 orbit evidence by `base_instance_id + variant` only.
The orbit table has no `repeat_id`, so this is partial overlap evidence rather
than a full v2 runtime conclusion.

- runtime bases: `35`
- orbit-overlap bases: `19`
- runtime variant rows: `105`
- orbit-overlap variant rows: `57`
- missing orbit bases: `dominating_set_hex_4x6_s6, even_colouring_torus_4x6_split, even_colouring_torus_5x5_split, php_exit_all_p6_h5, php_exit_single_p7_h6, random_3sat_control_v100_c600_seed1914, random_3sat_control_v20_c85_seed1901, random_3sat_control_v30_c128_seed1902, random_3sat_control_v35_c149_seed1911, random_3sat_control_v40_c170_seed1903, random_3sat_control_v60_c180_seed1912, random_3sat_control_v80_c340_seed1913, subset_cardinality_bw10, subset_cardinality_bw12, vertex_cover_torus_4x5_k6_event, vertex_cover_torus_4x5_k8_event`

### Strict Candidate Orbit Overlap

| family | base_instance_id | variant | repeat_rows | primary_final_cpu_mean_delta | primary_final_decisions_mean_delta | primary_final_conflicts_mean_delta | orbit_rows | orbit_valid_rows | event_row_valid_rows | event_identity_positive_rows | orbit_event_identity_gain_max | orbit_adapter_identity_gain_max | orbit_adapter_mu_identity_gain_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k5_color4 | base | 3 | -0.000339 | -2 | -3 | 1 | 1 | 1 | 1 | 12.23 | 0.9021 | 0.9021 |
| complete_coloring | k5_color4 | perm_seed1730 | 3 | -0.0003833 | 5 | 4 | 1 | 1 | 1 | 1 | 11.23 | 0.9481 | 0.9481 |
| complete_coloring | k5_color4 | perm_seed1731 | 3 | -0.0006163 | -9 | -3 | 1 | 1 | 1 | 1 | 12.02 | 0.8249 | 0.8249 |

## Diagnostic Conclusion

The v2 data contains a small strict-positive subset where the adapter changes final
search, including the named strict candidates. The signal is not a protocol-time
win: event collection overhead still dominates when comparing to the static weighted
path. The random 3SAT control strict case also means this evidence should be treated
as search-change evidence, not symmetry-specific solver-speed evidence.

The next representation audit, if pursued, should be targeted before any gate or
selector work: prioritize `dominating_set_hex_3x6_s4` and `subset_cardinality_bw12`,
then nearby same-family/scale bases. The v2-missing orbit bases remain partial-coverage
gaps rather than runtime conclusions.
