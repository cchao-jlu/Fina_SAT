# GRPO Control Wins vs Symmetry Family Losses

This is a targeted post-hoc diagnosis of existing GRPO runtime outputs. It does not expand the benchmark and does not train or build a gate.

## Inputs

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_EventVarSpeedupFull/best.pt`
- per-instance runtime CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_grpo_speedup_best_harder_baseline_per_instance.csv`

## Headline

- random-control bases where adapter final CPU beats plain: 6/7
- random-control bases where adapter final CPU beats static weighted: 4/7
- hex/torus bases audited: 7
- hex/torus bases where adapter final solve is worse than static weighted: 4/7
- hex/torus bases with adapter final CPU within 80% of cap: 6/7
- mean hex/torus event-collection overhead delta: 4.44576s
- mean hex/torus adapter-minus-static final CPU delta: -9.20635e-05s

Interpretation: random-control wins look generic rather than symmetry-specific unless they correlate with valid symmetry evidence. The audited random controls show adapter-induced phase/weight shifts, while hex/torus losses are dominated by large event-collection overhead plus several cases where the adapter final solve is itself worse than static weighted.

## Random Controls

| base_instance_id | scale | mean_adapter_minus_plain_final_cpu_time | mean_adapter_minus_plain_protocol_accounted_time | mean_adapter_minus_static_final_cpu_time | mean_adapter_minus_plain_final_decisions | mean_adapter_minus_plain_final_conflicts | mean_cached_minus_static_protocol_accounted_time | mean_warmup_cpu_time__event_adapter_final | adapter_final_solve_better_than_static |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v260_c1097_seed3305 | large | -3.45499 | -2.55668 | -0.800301 | -172812 | -150468 | 0.887847 | 0.886884 | True |
| random_3sat_control_v300_c1266_seed3307 | large | -0.959904 | -0.938756 | 0.000421778 | -47972 | -41283.7 | 0.0106858 | 0.00946767 | False |
| random_3sat_control_v220_c928_seed3303 | large | -0.441302 | -0.426557 | -0.000709 | -29025 | -25076.7 | 0.00434011 | 0.00346267 | True |
| random_3sat_control_v180_c760_seed3301 | large | -0.344027 | -0.32242 | 0.0124328 | -26647.7 | -23012.3 | 0.0113539 | 0.0104996 | False |
| random_3sat_control_v220_c942_seed3304 | large | -0.016327 | 0.313173 | 0.121383 | 2044.33 | 3038.33 | 0.319083 | 0.318161 | False |
| random_3sat_control_v160_c704_seed2615 | large | -0.0140647 | 0.035349 | -0.00321333 | -1672.33 | -1310.33 | 0.0389868 | 0.0381573 | True |
| random_3sat_control_v260_c1113_seed3306 | large | 0.504612 | 2.62307 | -0.177066 | 38477 | 40327 | 2.10811 | 2.10711 | True |

## Random Control Parameter Shifts

| base_instance_id | rows | phase_flip_frac_mean | weight_delta_abs_mean | weight_ratio_mean | weight_ratio_max | weight_rank_spearman_mean | event_l2_weight_abs_delta_spearman_mean | final_cpu_delta_mean | decisions_delta_mean | conflicts_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v260_c1097_seed3305 | 9 | 0.024359 | 0.823682 | 1.06352 | 2.71864 | 0.590943 | 0.0708009 | -3.45499 | -172812 | -150468 |
| random_3sat_control_v300_c1266_seed3307 | 9 | 0.0133333 | 0.816163 | 1.36324 | 2.71835 | 0.610471 | 0.328057 | -0.959904 | -47972 | -41283.7 |
| random_3sat_control_v220_c928_seed3303 | 9 | 0.00909091 | 0.645242 | 1.11168 | 2.71872 | 0.666903 | 0.250947 | -0.441302 | -29025 | -25076.7 |
| random_3sat_control_v180_c760_seed3301 | 9 | 0.00555556 | 0.816884 | 0.976453 | 2.71862 | 0.719363 | 0.170265 | -0.344027 | -26647.7 | -23012.3 |
| random_3sat_control_v220_c942_seed3304 | 9 | 0.0424242 | 0.844151 | 1.11343 | 2.71829 | 0.494319 | 0.060328 | -0.016327 | 2044.33 | 3038.33 |
| random_3sat_control_v160_c704_seed2615 | 9 | 0.00416667 | 0.866047 | 1.51751 | 2.71896 | 0.507582 | 0.193454 | -0.0140647 | -1672.33 | -1310.33 |
| random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 1.19988 | 2.00323 | 2.7182 | 0.63395 | 0.794727 | 0.504612 | 38477 | 40327 |

## Dominating Set Hex / Vertex Cover Torus

| family | base_instance_id | scale | mean_adapter_minus_plain_final_cpu_time | mean_adapter_minus_plain_protocol_accounted_time | mean_adapter_minus_static_final_cpu_time | mean_adapter_minus_cached_final_cpu_time | mean_cached_minus_static_protocol_accounted_time | mean_warmup_cpu_time__event_adapter_final | adapter_near_cap_rows | cap_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_5x4_s5 | large | 7.72676 | 12.7569 | 0.00072 | 0.00072 | 4.99994 | 4.99926 | 9 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | large | 7.63431 | 12.6613 | -0.000525556 | -0.000525556 | 4.99704 | 4.99635 | 9 | True |
| dominating_set_hex | dominating_set_hex_3x7_s5 | large | 4.66866 | 9.70971 | 0.0001 | 0.0001 | 5.00135 | 5.00066 | 9 | True |
| dominating_set_hex | dominating_set_hex_3x6_s4 | large | 0.995563 | 2.13812 | 0.000225556 | 0.000225556 | 1.12838 | 1.12768 | 0 | False |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | large | 8.60944 | 13.6334 | 0.000228889 | 0.000228889 | 4.99728 | 4.9966 | 9 | True |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | large | 6.90153 | 11.9366 | -0.000452222 | -0.000452222 | 4.99711 | 4.99645 | 9 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | large | 2.46609 | 7.52546 | -0.000941111 | -0.000941111 | 4.9992 | 4.99855 | 9 | True |

## Family-Level Decomposition

| family | bases | mean_adapter_minus_plain_protocol | mean_adapter_minus_plain_final_cpu | mean_adapter_minus_static_final_cpu | mean_cached_minus_static_protocol | final_solve_better_than_static_bases | final_solve_worse_than_static_bases | final_solve_better_than_plain_bases | cap_risk_bases | mean_warmup_cpu | mean_adapter_inference_wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 7 | -0.181831 | -0.675143 | -0.121007 | 0.482915 | 4 | 3 | 6 | 0 | 0.481963 | 0.00236918 |
| dominating_set_hex | 4 | 9.31651 | 5.25632 | 0.00013 | 4.03168 | 1 | 3 | 0 | 3 | 4.03099 | 0.00351404 |
| vertex_cover_torus | 3 | 11.0318 | 5.99235 | -0.000388148 | 4.99786 | 2 | 1 | 0 | 3 | 4.9972 | 0.00468076 |

## Notes

- `adapter_minus_static_final_cpu_time` isolates adapter final-solve effect after static weighted guidance.
- `cached_minus_static_protocol_accounted_time` is the event warmup/attach overhead paid before adapter inference.
- `phase_flip_frac` and weight deltas come from replaying the short warmup and doing model forward only; no final solver benchmark was rerun for these parameter-shift rows.
- A negative final CPU delta on non-symmetric controls is generic search perturbation evidence, not SAT symmetry evidence.
