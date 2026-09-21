# Runtime Drift, Strict-Positive Calibration, and Subset Permutation Diagnosis v2

## Scope

This audit does not train, does not build a gate/selector, does not expand the
runtime benchmark, and does not make a solver speedup claim. It checks current
runtime snapshot lineage, calibrates the current strict-positive rows, and digs
into the `subset_cardinality_bw12` permutation failure mode.

## Runtime Snapshot Lineage

| role | path | size_bytes | mtime_ns | sha256 | rows | base_instances | repeats | solver_path_roles | weighted_no_pre_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attribution | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv | 198440 | 1781249259625026667 | 35769697c9252a370e936cbdf00209e11917789f0b6c39b18d3bf15cf1e8f98d | nan | nan | nan | nan | nan |
| per_instance | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv | 1284699 | 1781249259501028559 | e68a8b07c9b94847f26a568443c48e0688d214d260db7714e71be225af34040d | nan | nan | nan | nan | nan |
| manifest | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv | 68014 | 1781248702401499797 | 6ff13b4003bf2c8bc0acd598e923fcf2123769be6d0026b284e26b1362cafd18 | nan | nan | nan | nan | nan |
| positive_base_summary | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_positive_v2_base_summary.csv | 34161 | 1781249440518600577 | 9020333ce5f393a776e3400e711d18724ed52f8bc06b23dfc2f2266886352917 | nan | nan | nan | nan | nan |
| positive_observations | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_positive_v2_observations.csv | 261761 | 1781249440534600399 | 4eb53f58e81d68862cdd0ee1a78865279050fa2ee68d2b091be221d102c794a6 | nan | nan | nan | nan | nan |
| targeted_candidate_summary | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_targeted_mechanism_v2_candidate_summary.csv | 1588 | 1781250572679683045 | ece85f8754795b5f0e5f28dee9027ed3e149592c33948a17780acf047736df7a | nan | nan | nan | nan | nan |
| targeted_repeat_join | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_targeted_mechanism_v2_repeat_join.csv | 13763 | 1781250572683682989 | 60d829253c49e7e07b839076ee24a9a315180cf90b1451b433fd8d4fd2725184 | nan | nan | nan | nan | nan |
| targeted_orbit_rows | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv | 403400 | 1781250572699682761 | a3d610d4b7708f4949c9dfab439c15cff035735f88da0554651017db86c7ccb7 | nan | nan | nan | nan | nan |
| current_runtime_protocol_signature | /home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_per_instance.csv | 1284699 | 1781249259501028559 | e68a8b07c9b94847f26a568443c48e0688d214d260db7714e71be225af34040d | 1575 | 35 | 0,1,2 | patched_pretrue_main | False |

The current positive subset and targeted mechanism tables are derived after the
refreshed v2 runtime CSV. The current runtime signature is fixed to repeats
`0,1,2`, variants `base,perm_seed1730,perm_seed1731`, solver path
`patched_pretrue_main`, and `weighted_no_pre=False`. Earlier strict-like
status is therefore treated as a pre-refresh observation unless an archived
old runtime CSV is restored for exact numeric diffing.

## Runtime Consistency

| source | rows | unique_keys | missing_from_runtime_keys | extra_runtime_keys_not_in_source | base_instances | variants | repeats | methods_per_key_min | methods_per_key_max | solver_seeds | warmup_seeds | final_seeds | solver_path_roles | weighted_no_pre_values | final_cpu_lims | warmup_cpu_lims | warmup_conflict_budgets | protocol_consistent_with_runtime | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attribution | 315 | 315 | 0 | 0 | 35 | base,perm_seed1730,perm_seed1731 | 0,1,2 | 5 | 5 | 1,2,3 | 1,2,3 | 1,2,3 | patched_pretrue_main | False | 5 | 5 | 20 | True | nan |
| positive_observations | 315 | 315 | 0 | 0 | 35 | base,perm_seed1730,perm_seed1731 | 0,1,2 | 5 | 5 | 1,2,3 | 1,2,3 | 1,2,3 | patched_pretrue_main | False | 5 | 5 | 20 | True | nan |
| targeted_mechanism_repeat_join | 27 | 27 | 0 | 288 | 3 | base,perm_seed1730,perm_seed1731 | 0,1,2 | 5 | 5 | 1,2,3 | 1,2,3 | 1,2,3 | patched_pretrue_main | False | 5 | 5 | 20 | True | nan |
| manifest_full | 108 | 108 | 3 | 0 | 36 | base,perm_seed1730,perm_seed1731 |  | 5 | 5 | 1,2,3 | 1,2,3 | 1,2,3 | patched_pretrue_main | False | 5 | 5 | 20 | False | full labeled manifest includes static_only_stress rows excluded from v2 full runtime |
| manifest_runtime_eligible | 105 | 105 | 0 | 0 | 35 | base,perm_seed1730,perm_seed1731 |  | 5 | 5 | 1,2,3 | 1,2,3 | 1,2,3 | patched_pretrue_main | False | 5 | 5 | 20 | True | static_only_stress excluded |

The positive subset and targeted audit keys join back to the current v2 runtime
snapshot. Positive observations cover all `315` base/variant/repeat keys; targeted
mechanism audit covers only the three named diagnostic candidates by design. Seed
columns are retained in targeted replay rows and match the current runtime keys.
The labeled manifest has one static-only stress base (`dominating_set_hex_4x7_s7`),
which is intentionally excluded from the v2 full runtime; the runtime-eligible
manifest keys match the current runtime keys.

## Named Candidate Drift

| base_instance_id | family | control_type | prior_named_status | current_primary_classification | current_secondary_classification | current_majority_threshold | current_cpu_down_rows | current_cpu_up_rows | current_decisions_down_rows | current_decisions_up_rows | current_conflicts_down_rows | current_conflicts_up_rows | current_mean_cpu_delta | current_mean_decisions_delta | current_mean_conflicts_delta | targeted_qualification_tier | targeted_mechanism_label | drift_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex_3x6_s4 | dominating_set_hex | weak_symmetry | pre-refresh strict-like candidate | negative | negative | 5 | 3 | 6 | 6 | 3 | 9 | 0 | 0.007801 | -1 | -2.667 | strong_named_runtime_regressed | mechanism partially aligned | current snapshot is not strict-positive; CPU direction fails majority |
| random_3sat_control_v20_c85_seed1901 | random_3sat_control | non_symmetric_control | pre-refresh strict-like candidate | negative | negative | 5 | 4 | 5 | 9 | 0 | 0 | 0 | -8.556e-05 | -2 | 0 | control_perturbation | mechanism partially aligned | current snapshot is not strict-positive; CPU direction fails majority |
| subset_cardinality_bw12 | subset_cardinality | weak_symmetry | pre-refresh strict-like candidate | negative | negative | 5 | 2 | 7 | 6 | 3 | 6 | 3 | 0.001179 | -28.33 | -14 | weak_named_runtime_regressed | mechanism partially aligned | current snapshot is not strict-positive; CPU direction fails majority |

The three named candidates no longer satisfy current `strict_positive` because
final CPU direction is not majority-down in the refreshed snapshot. The search
signals mostly remain visible for the two symmetry candidates, so the drift is
best read as runtime/CPU snapshot instability plus overhead sensitivity, not as
proof of solver speedup.

## Current Strict-Positive Calibration

| family | base_instance_id | control_type | strict_role | primary_classification | repeat_rows | variants | cpu_down_rows | decisions_down_rows | conflicts_down_rows | event_identity_positive_rows | adapter_identity_positive_rows | mean_event_identity_gain_max | mean_adapter_identity_gain_max | mean_primary_delta_final_cpu | mean_primary_delta_final_decisions | mean_primary_delta_final_conflicts | mechanism_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v60_c180_seed1912 | non_symmetric_control | perturbation_baseline | strict_positive | 9 | 3 | 7 | 3 | 9 | 0 | 0 | 0 | 0 | -0.0007133 | -0.6667 | -5 | mechanism partially aligned |
| complete_coloring | k5_color4 | strong_symmetry | symmetry_calibration | strict_positive | 9 | 3 | 5 | 6 | 6 | 9 | 9 | 11.83 | 0.8917 | -0.0004462 | -2 | -0.6667 | mechanism aligned |

`complete_coloring/k5_color4` is the only current symmetry strict-positive
calibration row. `random_3sat_control_v60_c180_seed1912` is a non-symmetric
perturbation baseline and must not be folded into symmetry-positive evidence.

## Subset Permutation Failure Diagnosis

| base_instance_id | variant | repeat_rows | search_worse_rows | decisions_down_rows | decisions_up_rows | conflicts_down_rows | conflicts_up_rows | mean_event_identity_gain_max | mean_adapter_identity_gain_max | mean_event_l2 | mean_gate_evidence | mean_abs_delta_mu | mean_abs_delta_rho | max_abs_delta_mu | max_abs_delta_rho | valid_event_orbit_rows | event_positive_orbit_rows | failure_signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality_bw12 | base | 3 | 0 | 3 | 0 | 3 | 0 | 15.26 | 0.9309 | 3623 | 4.804 | 0.904 | 0 | 1 | 0 | 3 | 3 | high_identity_search_improved |
| subset_cardinality_bw12 | perm_seed1730 | 3 | 3 | 0 | 3 | 0 | 3 | 41.06 | 0.7796 | 3254 | 4.796 | 0.8758 | 0 | 1 | 0 | 3 | 3 | high_identity_high_adapter_search_worse |
| subset_cardinality_bw12 | perm_seed1731 | 3 | 0 | 3 | 0 | 3 | 0 | 35.81 | 0.7178 | 3282 | 4.663 | 0.8803 | 0 | 1 | 0 | 3 | 3 | high_identity_search_improved |

Permutation-aligned variable ranking checks:

| repeat_id | orbit | left_variant | right_variant | aligned_variables | adapted_mu_spearman | delta_mu_spearman | delta_mu_sign_agreement | left_decisions_delta | right_decisions_delta | left_conflicts_delta | right_conflicts_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | subset_cardinality_refined_o01_size4 | base | perm_seed1730 | 4 | -0.4 | -0.4 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o01_size4 | base | perm_seed1731 | 4 | 0.8 | 0.8 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o01_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.2 | 0.2 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o02_size1 | base | perm_seed1730 | 1 | nan | nan | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o02_size1 | base | perm_seed1731 | 1 | nan | nan | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o02_size1 | perm_seed1730 | perm_seed1731 | 1 | nan | nan | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o03_size12 | base | perm_seed1730 | 12 | 0.9712 | 0.1429 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o03_size12 | base | perm_seed1731 | 12 | 0.9606 | -0.1841 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o03_size12 | perm_seed1730 | perm_seed1731 | 12 | 0.9893 | 0.6975 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o04_size4 | base | perm_seed1730 | 4 | 1 | 0.9487 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o04_size4 | base | perm_seed1731 | 4 | 0.9428 | -0.3162 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o04_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.9428 | -0.2 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o05_size6 | base | perm_seed1730 | 6 | 0.3769 | 0.3769 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o05_size6 | base | perm_seed1731 | 6 | 0.1518 | -0.02899 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o05_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.5236 | 0.4265 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o06_size2 | base | perm_seed1730 | 2 | 1 | 1 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o06_size2 | base | perm_seed1731 | 2 | 1 | 1 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o06_size2 | perm_seed1730 | perm_seed1731 | 2 | 1 | 1 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o07_size8 | base | perm_seed1730 | 8 | 0.9542 | 0.4626 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o07_size8 | base | perm_seed1731 | 8 | 0.9542 | 0.4626 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o07_size8 | perm_seed1730 | perm_seed1731 | 8 | 0.8974 | 0.4527 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o08_size6 | base | perm_seed1730 | 6 | -0.6377 | -0.7143 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o08_size6 | base | perm_seed1731 | 6 | -0.3769 | -0.4857 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o08_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.9429 | 0.9429 | 1 | 13 | -43 | 1 | -21 |
| 0 | subset_cardinality_refined_o09_size6 | base | perm_seed1730 | 6 | 0.05798 | 0.08571 | 1 | -55 | 13 | -22 | 1 |
| 0 | subset_cardinality_refined_o09_size6 | base | perm_seed1731 | 6 | 0.3676 | 0.2571 | 1 | -55 | -43 | -22 | -21 |
| 0 | subset_cardinality_refined_o09_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.7537 | 0.8286 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o01_size4 | base | perm_seed1730 | 4 | -0.4 | -0.4 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o01_size4 | base | perm_seed1731 | 4 | 0.8 | 0.8 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o01_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.2 | 0.2 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o02_size1 | base | perm_seed1730 | 1 | nan | nan | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o02_size1 | base | perm_seed1731 | 1 | nan | nan | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o02_size1 | perm_seed1730 | perm_seed1731 | 1 | nan | nan | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o03_size12 | base | perm_seed1730 | 12 | 0.9712 | 0.1429 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o03_size12 | base | perm_seed1731 | 12 | 0.9606 | -0.1841 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o03_size12 | perm_seed1730 | perm_seed1731 | 12 | 0.9893 | 0.6975 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o04_size4 | base | perm_seed1730 | 4 | 1 | 0.9487 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o04_size4 | base | perm_seed1731 | 4 | 0.9428 | -0.3162 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o04_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.9428 | -0.2 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o05_size6 | base | perm_seed1730 | 6 | 0.3769 | 0.3769 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o05_size6 | base | perm_seed1731 | 6 | 0.1518 | -0.02899 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o05_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.5236 | 0.4265 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o06_size2 | base | perm_seed1730 | 2 | 1 | 1 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o06_size2 | base | perm_seed1731 | 2 | 1 | 1 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o06_size2 | perm_seed1730 | perm_seed1731 | 2 | 1 | 1 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o07_size8 | base | perm_seed1730 | 8 | 0.9542 | 0.4626 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o07_size8 | base | perm_seed1731 | 8 | 0.9542 | 0.4626 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o07_size8 | perm_seed1730 | perm_seed1731 | 8 | 0.8974 | 0.4527 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o08_size6 | base | perm_seed1730 | 6 | -0.6377 | -0.7143 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o08_size6 | base | perm_seed1731 | 6 | -0.3769 | -0.4857 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o08_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.9429 | 0.9429 | 1 | 13 | -43 | 1 | -21 |
| 1 | subset_cardinality_refined_o09_size6 | base | perm_seed1730 | 6 | 0.05798 | 0.08571 | 1 | -55 | 13 | -22 | 1 |
| 1 | subset_cardinality_refined_o09_size6 | base | perm_seed1731 | 6 | 0.3676 | 0.2571 | 1 | -55 | -43 | -22 | -21 |
| 1 | subset_cardinality_refined_o09_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.7537 | 0.8286 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o01_size4 | base | perm_seed1730 | 4 | -0.4 | -0.4 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o01_size4 | base | perm_seed1731 | 4 | 0.8 | 0.8 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o01_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.2 | 0.2 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o02_size1 | base | perm_seed1730 | 1 | nan | nan | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o02_size1 | base | perm_seed1731 | 1 | nan | nan | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o02_size1 | perm_seed1730 | perm_seed1731 | 1 | nan | nan | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o03_size12 | base | perm_seed1730 | 12 | 0.9712 | 0.1429 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o03_size12 | base | perm_seed1731 | 12 | 0.9606 | -0.1841 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o03_size12 | perm_seed1730 | perm_seed1731 | 12 | 0.9893 | 0.6975 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o04_size4 | base | perm_seed1730 | 4 | 1 | 0.9487 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o04_size4 | base | perm_seed1731 | 4 | 0.9428 | -0.3162 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o04_size4 | perm_seed1730 | perm_seed1731 | 4 | 0.9428 | -0.2 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o05_size6 | base | perm_seed1730 | 6 | 0.3769 | 0.3769 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o05_size6 | base | perm_seed1731 | 6 | 0.1518 | -0.02899 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o05_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.5236 | 0.4265 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o06_size2 | base | perm_seed1730 | 2 | 1 | 1 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o06_size2 | base | perm_seed1731 | 2 | 1 | 1 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o06_size2 | perm_seed1730 | perm_seed1731 | 2 | 1 | 1 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o07_size8 | base | perm_seed1730 | 8 | 0.9542 | 0.4626 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o07_size8 | base | perm_seed1731 | 8 | 0.9542 | 0.4626 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o07_size8 | perm_seed1730 | perm_seed1731 | 8 | 0.8974 | 0.4527 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o08_size6 | base | perm_seed1730 | 6 | -0.6377 | -0.7143 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o08_size6 | base | perm_seed1731 | 6 | -0.3769 | -0.4857 | 1 | -55 | -43 | -22 | -21 |
| 2 | subset_cardinality_refined_o08_size6 | perm_seed1730 | perm_seed1731 | 6 | 0.9429 | 0.9429 | 1 | 13 | -43 | 1 | -21 |
| 2 | subset_cardinality_refined_o09_size6 | base | perm_seed1730 | 6 | 0.05798 | 0.08571 | 1 | -55 | 13 | -22 | 1 |
| 2 | subset_cardinality_refined_o09_size6 | base | perm_seed1731 | 6 | 0.3676 | 0.2571 | 1 | -55 | -43 | -22 | -21 |

`perm_seed1730` is the useful failure case: event identity and adapter separation
are high, but decisions/conflicts move in the wrong direction. If aligned adapted
mu/rho rankings are inconsistent with the improving variants, the adapter objective
needs stronger permutation consistency. If rankings are consistent while search
still worsens, the issue is likely over-reaction/search sensitivity, motivating a
negative-control restraint rather than a gate.

## Decision

- Do not train a gate/selector from this state.
- Treat current strict positives as calibration only.
- Focus next on adapter objective/permutation robustness and negative-control restraint.
- Keep event overhead as a separate blocker before any renewed runtime viability claim.

## Artifacts

- snapshot_lineage: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_drift_v2_snapshot_lineage.csv`
- runtime_consistency: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_drift_v2_consistency.csv`
- named_candidate_drift: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_drift_v2_named_candidates.csv`
- current_strict_summary: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_current_strict_positive_v2_summary.csv`
- current_strict_repeat_join: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_current_strict_positive_v2_repeat_join.csv`
- current_strict_orbit_rows: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_current_strict_positive_v2_orbit_rows.csv`
- subset_failure: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_subset_bw12_permutation_failure_v2.csv`
- subset_variable_rows: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_subset_bw12_variable_rows_v2.csv`
- subset_permutation_alignment: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_subset_bw12_permutation_alignment_v2.csv`
