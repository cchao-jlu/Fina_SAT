# GRPO Control Wins vs Symmetry Family Losses

This is a targeted post-hoc diagnosis of existing GRPO runtime outputs. It does not expand the benchmark and does not train or build a gate.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EventVarSpeedupFull/best.pt`
- per-instance runtime CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_v2_per_instance.csv`

## Headline

- random-control bases where adapter final CPU beats plain: 1/7
- random-control bases where adapter final CPU beats static weighted: 2/7
- hex/torus bases audited: 11
- hex/torus bases where adapter final solve is worse than static weighted: 5/11
- hex/torus bases with adapter final CPU within 80% of cap: 5/11
- mean hex/torus event-collection overhead delta: 2.46548s
- mean hex/torus adapter-minus-static final CPU delta: -0.00105047s

Interpretation: random-control wins look generic rather than symmetry-specific unless they correlate with valid symmetry evidence. The audited random controls show adapter-induced phase/weight shifts, while hex/torus losses are dominated by large event-collection overhead plus several cases where the adapter final solve is itself worse than static weighted.

## Random Controls

| base_instance_id | scale | mean_adapter_minus_plain_final_cpu_time | mean_adapter_minus_plain_protocol_accounted_time | mean_adapter_minus_static_final_cpu_time | mean_adapter_minus_plain_final_decisions | mean_adapter_minus_plain_final_conflicts | mean_cached_minus_static_protocol_accounted_time | mean_warmup_cpu_time__event_adapter_final | adapter_final_solve_better_than_static |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v20_c85_seed1901 | small | -0.000134667 | 0.0100029 | -0.000257444 | -7 | -9.33333 | 0.00203585 | 0.00144122 | True |
| random_3sat_control_v30_c128_seed1902 | medium | 0.000373111 | 0.0110458 | 0.000757556 | -15.3333 | -13.3333 | 0.00232545 | 0.00164289 | False |
| random_3sat_control_v60_c180_seed1912 | large | 0.000515444 | 0.011925 | -0.00121411 | 3.66667 | 3.66667 | 0.0031143 | 0.00239444 | True |
| random_3sat_control_v80_c340_seed1913 | large | 0.000715778 | 0.0138128 | 0.000494667 | -155 | -130 | 0.00412481 | 0.00338356 | False |
| random_3sat_control_v35_c149_seed1911 | medium | 0.000800333 | 0.0120652 | 0.00153489 | -9.33333 | -6.66667 | 0.00285379 | 0.00217456 | False |
| random_3sat_control_v40_c170_seed1903 | medium | 0.00186289 | 0.0126813 | 0.000435667 | -33.6667 | -27 | 0.00256325 | 0.00194633 | False |
| random_3sat_control_v100_c600_seed1914 | large | 0.00302756 | 0.0193898 | 0.00273322 | 15 | 21 | 0.00554375 | 0.00477367 | False |

## Random Control Parameter Shifts

| base_instance_id | rows | phase_flip_frac_mean | weight_delta_abs_mean | weight_ratio_mean | weight_ratio_max | weight_rank_spearman_mean | event_l2_weight_abs_delta_spearman_mean | final_cpu_delta_mean | decisions_delta_mean | conflicts_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v20_c85_seed1901 | 9 | 0 | 0.748276 | 1.23366 | 2.7184 | 0.451128 | 0.509774 | -0.000134667 | -7 | -9.33333 |
| random_3sat_control_v30_c128_seed1902 | 9 | 0 | 0.658804 | 0.973739 | 2.71822 | 0.532963 | 0.429588 | 0.000373111 | -15.3333 | -13.3333 |
| random_3sat_control_v60_c180_seed1912 | 9 | 0.0833333 | 0.240198 | 1.17674 | 2.3673 | 0.34341 | 0.251533 | 0.000515444 | 3.66667 | 3.66667 |
| random_3sat_control_v80_c340_seed1913 | 9 | 0 | 0.737889 | 1.19769 | 2.7183 | 0.688529 | 0.151703 | 0.000715778 | -155 | -130 |
| random_3sat_control_v35_c149_seed1911 | 9 | 0 | 0.691208 | 1.035 | 2.71846 | 0.798133 | 0.414099 | 0.000800333 | -9.33333 | -6.66667 |
| random_3sat_control_v40_c170_seed1903 | 9 | 0 | 0.664015 | 1.02049 | 2.71864 | 0.623139 | 0.386992 | 0.00186289 | -33.6667 | -27 |
| random_3sat_control_v100_c600_seed1914 | 9 | 0 | 0.313538 | 1.07806 | 2.71779 | 0.430415 | -0.0861046 | 0.00302756 | 15 | 21 |

## Dominating Set Hex / Vertex Cover Torus

| family | base_instance_id | scale | mean_adapter_minus_plain_final_cpu_time | mean_adapter_minus_plain_protocol_accounted_time | mean_adapter_minus_static_final_cpu_time | mean_adapter_minus_cached_final_cpu_time | mean_cached_minus_static_protocol_accounted_time | mean_warmup_cpu_time__event_adapter_final | adapter_near_cap_rows | cap_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_4x5_s5 | large | 2.64095 | 7.66794 | 0.00101111 | 0.00101111 | 4.99724 | 4.99657 | 9 | True |
| dominating_set_hex | dominating_set_hex_4x6_s6 | stress | 0.00491556 | 5.27593 | -0.00299444 | -0.00299444 | 4.99581 | 4.99513 | 9 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | large | 0.980933 | 2.11656 | -0.00223556 | -0.00223556 | 1.12406 | 1.12337 | 0 | False |
| dominating_set_hex | dominating_set_hex_3x5_s3 | medium | 0.0330842 | 0.0937706 | -0.006489 | -0.006489 | 0.0473762 | 0.0467651 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | stress | 0.00278889 | 5.16372 | -0.00415667 | -0.00415667 | 5.00527 | 5.00463 | 9 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | stress | 0.00824111 | 5.11358 | 0.00178333 | 0.00178333 | 5.00161 | 5.00096 | 9 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | large | 0.000654444 | 5.05616 | -0.00115111 | -0.00115111 | 4.99705 | 4.99639 | 9 | True |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | large | 0.529287 | 1.13872 | 0.00221322 | 0.00221322 | 0.598014 | 0.597364 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | large | 0.273769 | 0.600426 | -0.000871111 | -0.000871111 | 0.31537 | 0.314724 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | medium | 0.0150557 | 0.0474114 | 0.000453444 | 0.000453444 | 0.0226601 | 0.0220411 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | medium | 0.0129516 | 0.03855 | 0.000881556 | 0.000881556 | 0.0157762 | 0.0151169 | 0 | False |

## Family-Level Decomposition

| family | bases | mean_adapter_minus_plain_protocol | mean_adapter_minus_plain_final_cpu | mean_adapter_minus_static_final_cpu | mean_cached_minus_static_protocol | final_solve_better_than_static_bases | final_solve_worse_than_static_bases | final_solve_better_than_plain_bases | cap_risk_bases | mean_warmup_cpu | mean_adapter_inference_wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 7 | 0.012989 | 0.00102292 | 0.000640635 | 0.00322303 | 2 | 5 | 1 | 0 | 0.00253667 | 0.00180559 |
| vertex_cover_torus | 7 | 2.45122 | 0.120393 | -0.000121048 | 2.27939 | 3 | 4 | 0 | 3 | 2.27875 | 0.00469884 |
| dominating_set_hex | 4 | 3.78855 | 0.914971 | -0.00267697 | 2.79112 | 3 | 1 | 0 | 2 | 2.79046 | 0.00674927 |

## Notes

- `adapter_minus_static_final_cpu_time` isolates adapter final-solve effect after static weighted guidance.
- `cached_minus_static_protocol_accounted_time` is the event warmup/attach overhead paid before adapter inference.
- `phase_flip_frac` and weight deltas come from replaying the short warmup and doing model forward only; no final solver benchmark was rerun for these parameter-shift rows.
- A negative final CPU delta on non-symmetric controls is generic search perturbation evidence, not SAT symmetry evidence.
