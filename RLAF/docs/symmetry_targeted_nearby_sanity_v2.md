# Targeted Nearby Sanity v2

## Scope

This is a small targeted mechanism sanity audit around the current hex/subset diagnostic targets. It replays only the short event warmup and orbit audit for selected nearby bases; it does not expand the full v2 runtime benchmark, does not train, does not build a gate/selector, and does not make a speedup claim.

- bases: `dominating_set_hex_3x5_s3, dominating_set_hex_3x6_s4, dominating_set_hex_4x5_s5, subset_cardinality_bw8, subset_cardinality_bw10, subset_cardinality_bw12`
- observations source: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_positive_v2_observations.csv`
- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv`
- wall time for this audit: `not rerun; report regenerated from existing CSVs`

## Base Summary

| family | base_instance_id | scale | runtime_primary_classification | mechanism_label | repeat_rows | variants | cpu_down_rows | cpu_up_rows | search_improved_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | event_positive_rows | adapter_positive_rows | event_identity_gain_max_mean | adapter_identity_gain_max_mean | event_row_valid_rows_sum | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | medium | timing_only_positive | mechanism partially aligned | 9 | 3 | 8 | 1 | 3 | 3 | -1 | -0.3333 | 9 | 9 | 1.972 | 0.3611 | 45 | 7.667 | 4 | 9 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | large | negative | mechanism partially aligned | 9 | 3 | 3 | 6 | 9 | 3 | -1 | -2.667 | 9 | 9 | 4.212 | 0.4852 | 54 | 12.67 | 7.667 | 9 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | large | negative | mechanism partially aligned | 9 | 3 | 4 | 5 | 6 | 3 | 0 | -1.333 | 9 | 9 | 1.887 | 0.4033 | 90 | 28 | 15 | 9 |
| subset_cardinality | subset_cardinality_bw10 | large | negative | mechanism partially aligned | 9 | 3 | 7 | 2 | 3 | 9 | 25.33 | 4.667 | 9 | 9 | 17.75 | 0.8887 | 54 | 167.7 | 143 | 9 |
| subset_cardinality | subset_cardinality_bw12 | large | negative | mechanism partially aligned | 9 | 3 | 2 | 7 | 6 | 3 | -28.33 | -14 | 9 | 9 | 30.71 | 0.8094 | 9 | 360.3 | 296.3 | 9 |
| subset_cardinality | subset_cardinality_bw8 | medium | negative | mechanism partially aligned | 9 | 3 | 2 | 7 | 9 | 6 | -2.333 | -5.333 | 9 | 9 | 5.635 | 1.069 | 36 | 90.67 | 72.67 | 9 |

## Hex Nearby

| family | base_instance_id | scale | runtime_primary_classification | mechanism_label | repeat_rows | variants | cpu_down_rows | cpu_up_rows | search_improved_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | event_positive_rows | adapter_positive_rows | event_identity_gain_max_mean | adapter_identity_gain_max_mean | event_row_valid_rows_sum | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | medium | timing_only_positive | mechanism partially aligned | 9 | 3 | 8 | 1 | 3 | 3 | -1 | -0.3333 | 9 | 9 | 1.972 | 0.3611 | 45 | 7.667 | 4 | 9 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | large | negative | mechanism partially aligned | 9 | 3 | 3 | 6 | 9 | 3 | -1 | -2.667 | 9 | 9 | 4.212 | 0.4852 | 54 | 12.67 | 7.667 | 9 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | large | negative | mechanism partially aligned | 9 | 3 | 4 | 5 | 6 | 3 | 0 | -1.333 | 9 | 9 | 1.887 | 0.4033 | 90 | 28 | 15 | 9 |

## Subset Nearby

| family | base_instance_id | scale | runtime_primary_classification | mechanism_label | repeat_rows | variants | cpu_down_rows | cpu_up_rows | search_improved_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | event_positive_rows | adapter_positive_rows | event_identity_gain_max_mean | adapter_identity_gain_max_mean | event_row_valid_rows_sum | warmup_decisions_mean | warmup_conflicts_mean | graph_gate_open_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality | subset_cardinality_bw10 | large | negative | mechanism partially aligned | 9 | 3 | 7 | 2 | 3 | 9 | 25.33 | 4.667 | 9 | 9 | 17.75 | 0.8887 | 54 | 167.7 | 143 | 9 |
| subset_cardinality | subset_cardinality_bw12 | large | negative | mechanism partially aligned | 9 | 3 | 2 | 7 | 6 | 3 | -28.33 | -14 | 9 | 9 | 30.71 | 0.8094 | 9 | 360.3 | 296.3 | 9 |
| subset_cardinality | subset_cardinality_bw8 | medium | negative | mechanism partially aligned | 9 | 3 | 2 | 7 | 9 | 6 | -2.333 | -5.333 | 9 | 9 | 5.635 | 1.069 | 36 | 90.67 | 72.67 | 9 |

## Variant Summary

| family | base_instance_id | variant | search_improved_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | event_positive_rows | adapter_positive_rows | event_identity_gain_max_mean | adapter_identity_gain_max_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | base | 0 | 3 | 1 | 0 | 3 | 3 | 1.396 | 0.2675 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1730 | 3 | 0 | -4 | -1 | 3 | 3 | 3.695 | 0.5177 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | perm_seed1731 | 0 | 0 | 0 | 0 | 3 | 3 | 0.8257 | 0.298 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | base | 3 | 0 | -1 | -2 | 3 | 3 | 3.281 | 0.3216 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1730 | 3 | 3 | 2 | -2 | 3 | 3 | 3.906 | 0.5371 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | perm_seed1731 | 3 | 0 | -4 | -4 | 3 | 3 | 5.449 | 0.5971 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | base | 0 | 3 | 16 | 14 | 3 | 3 | 1.85 | 0.3191 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | 3 | 0 | -8 | -9 | 3 | 3 | 1.979 | 0.3677 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | 3 | 0 | -8 | -9 | 3 | 3 | 1.831 | 0.5232 |
| subset_cardinality | subset_cardinality_bw10 | base | 3 | 3 | 13 | -1 | 3 | 3 | 19.89 | 0.983 |
| subset_cardinality | subset_cardinality_bw10 | perm_seed1730 | 0 | 3 | 37 | 8 | 3 | 3 | 14.74 | 0.7277 |
| subset_cardinality | subset_cardinality_bw10 | perm_seed1731 | 0 | 3 | 26 | 7 | 3 | 3 | 18.61 | 0.9556 |
| subset_cardinality | subset_cardinality_bw12 | base | 3 | 0 | -55 | -22 | 3 | 3 | 15.26 | 0.9309 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | 3 | 13 | 1 | 3 | 3 | 41.06 | 0.7796 |
| subset_cardinality | subset_cardinality_bw12 | perm_seed1731 | 3 | 0 | -43 | -21 | 3 | 3 | 35.81 | 0.7178 |
| subset_cardinality | subset_cardinality_bw8 | base | 3 | 3 | 5 | -5 | 3 | 3 | 4.938 | 1.12 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1730 | 3 | 0 | -13 | -9 | 3 | 3 | 5.988 | 1.12 |
| subset_cardinality | subset_cardinality_bw8 | perm_seed1731 | 3 | 3 | 1 | -2 | 3 | 3 | 5.98 | 0.9657 |

## Orbit Validity

| family | base_instance_id | event_row_valid_reason | rows | event_identity_gain_mean | event_identity_gain_max | adapter_identity_gain_mean | adapter_identity_gain_max | adapted_mu_range_max | static_mu_range_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_3x5_s3 | orbit_size_below_min | 45 | 0 | 0 | 0 | 0 | 0 | 0 |
| dominating_set_hex | dominating_set_hex_3x5_s3 | valid | 45 | 0.6893 | 3.695 | 0.1994 | 0.5177 | 0.5177 | 2.235e-08 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | orbit_size_below_min | 54 | 0 | 0 | 0 | 0 | 0 | 0 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | valid | 54 | 1.501 | 5.449 | 0.2505 | 0.5971 | 0.5971 | 3.353e-08 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | valid | 90 | 0.6786 | 1.979 | 0.1426 | 0.5232 | 0.5232 | 3.725e-08 |
| subset_cardinality | subset_cardinality_bw10 | orbit_size_below_min | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| subset_cardinality | subset_cardinality_bw10 | valid | 54 | 5.521 | 19.89 | 0.621 | 0.983 | 0.983 | 5.96e-08 |
| subset_cardinality | subset_cardinality_bw12 | orbit_size_below_min | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| subset_cardinality | subset_cardinality_bw12 | static_mu_not_collapsed | 63 | 8.917 | 41.06 | 0.3203 | 0.9309 | 0.9312 | 0.001987 |
| subset_cardinality | subset_cardinality_bw12 | valid | 9 | 0.4491 | 0.5722 | 0.4628 | 0.7796 | 0.7796 | 2.98e-08 |
| subset_cardinality | subset_cardinality_bw8 | orbit_size_below_min | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| subset_cardinality | subset_cardinality_bw8 | valid | 36 | 2.151 | 5.988 | 0.6963 | 1.12 | 1.12 | 2.98e-08 |

## Interpretation

- Hex partial alignment is not an isolated single row: nearby hex bases emit valid event-positive rows and adapter separation, but search direction is variant-mixed and CPU is not a stable positive signal.
- Subset nearby cases show the same core risk as `bw12`: event/adapter identity exists, but permutation variants can move final decisions/conflicts in opposite directions.
- These results support Objective Fix v1 and targeted re-audit; they do not justify full benchmark expansion or gate/selector training.
