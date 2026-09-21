# Adapter Objective and Robustness Diagnosis v2

## Scope

This is an offline objective-level diagnosis. It does not train, does not build
a gate/selector, does not expand full runtime, and does not make a solver speedup
claim. It reuses the current v2 runtime snapshot and targeted orbit/variable
audits to ask whether the adapter uses event identity signal in a stable,
permutation-robust, symmetry-specific way.

## Permutation Robustness

| left_variant | right_variant | orbit_pair_rows | valid_pair_rows | search_direction_mismatch_rows | mean_static_mu_spearman | mean_static_rho_spearman | mean_adapted_mu_spearman | mean_adapted_rho_spearman | mean_delta_mu_spearman | mean_delta_mu_sign_agreement | valid_mean_event_gain_abs_diff | valid_mean_adapter_gain_abs_diff | all_mean_event_gain_abs_diff | all_mean_adapter_gain_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | perm_seed1730 | 27 | 3 | 27 | 0.871 | 0.6234 | 0.4153 | 0.6234 | 0.2378 | 1 | 0.1463 | 0.7577 | 9.691 | 0.2281 |
| base | perm_seed1731 | 27 | 3 | 0 | 0.8626 | 0.704 | 0.6 | 0.704 | 0.1881 | 1 | 0.07671 | 0.565 | 7.424 | 0.1419 |
| perm_seed1730 | perm_seed1731 | 27 | 3 | 27 | 0.9143 | 0.8847 | 0.7812 | 0.8847 | 0.5435 | 1 | 0.223 | 0.1928 | 2.597 | 0.1469 |

`subset_cardinality_bw12::perm_seed1730` remains the key failure sample: the
same base under another variable permutation has event/adapter signal, but the
final decisions/conflicts move in the wrong direction. Static alignment is not
enough; adapted mu/delta alignment is weak for the failing pair.

## Subset Variant Summary

| variant | repeat_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | event_identity_gain_max_all | event_identity_gain_max_valid | event_identity_gain_max_invalid | adapter_identity_gain_max_all | adapter_identity_gain_max_valid | adapter_identity_gain_max_invalid | adapted_mu_range_max_valid | adapted_mu_range_max_invalid | valid_orbit_rows | invalid_orbit_rows | event_positive_valid_rows | event_positive_invalid_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | 3 | 0 | -55 | -22 | 15.26 | 0.426 | 15.26 | 0.9309 | 0.02189 | 0.9309 | 0.02189 | 0.9312 | 3 | 24 | 3 | 0 |
| perm_seed1730 | 3 | 3 | 13 | 1 | 41.06 | 0.5722 | 41.06 | 0.7796 | 0.7796 | 0.7303 | 0.7796 | 0.7305 | 3 | 24 | 3 | 0 |
| perm_seed1731 | 3 | 0 | -43 | -21 | 35.81 | 0.3492 | 35.81 | 0.7178 | 0.5868 | 0.7178 | 0.5868 | 0.718 | 3 | 24 | 3 | 0 |

The repeat-level identity maxima mix valid and invalid orbit rows. For subset
only one refined orbit is event-row-valid per variant; several larger
`static_mu_not_collapsed` rows carry much larger event identity ranges and must
not be used as positive identity training evidence.

## Valid/Invalid Orbit Contribution

| variant | event_row_valid_reason | rows | search_worse_rows | event_identity_gain_mean | event_identity_gain_max | adapter_identity_gain_mean | adapter_identity_gain_max | adapted_mu_range_mean | adapted_mu_range_max | static_mu_range_mean | static_mu_range_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | orbit_size_below_min | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| base | static_mu_not_collapsed | 21 | 0 | 5.751 | 15.26 | 0.3454 | 0.9309 | 0.3461 | 0.9312 | 0.0007234 | 0.001987 |
| base | valid | 3 | 0 | 0.426 | 0.426 | 0.02189 | 0.02189 | 0.02189 | 0.02189 | 2.98e-08 | 2.98e-08 |
| perm_seed1730 | orbit_size_below_min | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| perm_seed1730 | static_mu_not_collapsed | 21 | 21 | 11.61 | 41.06 | 0.3083 | 0.7303 | 0.3091 | 0.7305 | 0.0007233 | 0.001987 |
| perm_seed1730 | valid | 3 | 3 | 0.5722 | 0.5722 | 0.7796 | 0.7796 | 0.7796 | 0.7796 | 0 | 0 |
| perm_seed1731 | orbit_size_below_min | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| perm_seed1731 | static_mu_not_collapsed | 21 | 0 | 9.387 | 35.81 | 0.307 | 0.7178 | 0.3078 | 0.718 | 0.0007233 | 0.001987 |
| perm_seed1731 | valid | 3 | 0 | 0.3492 | 0.3492 | 0.5868 | 0.5868 | 0.5868 | 0.5868 | 0 | 0 |

## Over-Adaptation Rows

| variant | repeat_id | orbit | event_row_valid_reason | valid_orbit | search_worse | event_identity_gain | adapter_identity_gain | adapter_to_event_gain_ratio | adapted_mu_range | static_mu_range | primary_delta_final_decisions | primary_delta_final_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| perm_seed1730 | 0 | subset_cardinality_refined_o06_size2 | valid | True | True | 0.5722 | 0.7796 | 1.362 | 0.7796 | 0 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o06_size2 | valid | True | True | 0.5722 | 0.7796 | 1.362 | 0.7796 | 0 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o06_size2 | valid | True | True | 0.5722 | 0.7796 | 1.362 | 0.7796 | 0 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o08_size6 | static_mu_not_collapsed | False | True | 2.951 | 0.7303 | 0.2475 | 0.7305 | 0.0002577 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o08_size6 | static_mu_not_collapsed | False | True | 2.951 | 0.7303 | 0.2475 | 0.7305 | 0.0002577 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o08_size6 | static_mu_not_collapsed | False | True | 2.951 | 0.7303 | 0.2475 | 0.7305 | 0.0002577 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o09_size6 | static_mu_not_collapsed | False | True | 1.122 | 0.5815 | 0.5181 | 0.5817 | 0.0001667 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o09_size6 | static_mu_not_collapsed | False | True | 1.122 | 0.5815 | 0.5181 | 0.5817 | 0.0001667 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o09_size6 | static_mu_not_collapsed | False | True | 1.122 | 0.5815 | 0.5181 | 0.5817 | 0.0001667 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o05_size6 | static_mu_not_collapsed | False | True | 2.204 | 0.5292 | 0.2402 | 0.5295 | 0.0002672 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o05_size6 | static_mu_not_collapsed | False | True | 2.204 | 0.5292 | 0.2402 | 0.5295 | 0.0002672 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o05_size6 | static_mu_not_collapsed | False | True | 2.204 | 0.5292 | 0.2402 | 0.5295 | 0.0002672 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o01_size4 | static_mu_not_collapsed | False | True | 2.755 | 0.3175 | 0.1152 | 0.3177 | 0.0002508 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o01_size4 | static_mu_not_collapsed | False | True | 2.755 | 0.3175 | 0.1152 | 0.3177 | 0.0002508 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o01_size4 | static_mu_not_collapsed | False | True | 2.755 | 0.3175 | 0.1152 | 0.3177 | 0.0002508 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o07_size8 | static_mu_not_collapsed | False | True | 8.804 | 1.49e-08 | 1.693e-09 | 0.001708 | 0.001708 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o07_size8 | static_mu_not_collapsed | False | True | 8.804 | 1.49e-08 | 1.693e-09 | 0.001708 | 0.001708 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o07_size8 | static_mu_not_collapsed | False | True | 8.804 | 1.49e-08 | 1.693e-09 | 0.001708 | 0.001708 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o04_size4 | static_mu_not_collapsed | False | True | 41.06 | 7.451e-09 | 1.815e-10 | 0.0004266 | 0.0004266 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o04_size4 | static_mu_not_collapsed | False | True | 41.06 | 7.451e-09 | 1.815e-10 | 0.0004266 | 0.0004266 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o04_size4 | static_mu_not_collapsed | False | True | 41.06 | 7.451e-09 | 1.815e-10 | 0.0004266 | 0.0004266 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o02_size1 | orbit_size_below_min | False | True | 0 | 0 | nan | 0 | 0 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o02_size1 | orbit_size_below_min | False | True | 0 | 0 | nan | 0 | 0 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o02_size1 | orbit_size_below_min | False | True | 0 | 0 | nan | 0 | 0 | 13 | 1 |
| perm_seed1730 | 0 | subset_cardinality_refined_o03_size12 | static_mu_not_collapsed | False | True | 22.39 | -2.98e-08 | -1.331e-09 | 0.001987 | 0.001987 | 13 | 1 |
| perm_seed1730 | 1 | subset_cardinality_refined_o03_size12 | static_mu_not_collapsed | False | True | 22.39 | -2.98e-08 | -1.331e-09 | 0.001987 | 0.001987 | 13 | 1 |
| perm_seed1730 | 2 | subset_cardinality_refined_o03_size12 | static_mu_not_collapsed | False | True | 22.39 | -2.98e-08 | -1.331e-09 | 0.001987 | 0.001987 | 13 | 1 |
| perm_seed1731 | 0 | subset_cardinality_refined_o06_size2 | valid | True | False | 0.3492 | 0.5868 | 1.68 | 0.5868 | 0 | -43 | -21 |
| perm_seed1731 | 1 | subset_cardinality_refined_o06_size2 | valid | True | False | 0.3492 | 0.5868 | 1.68 | 0.5868 | 0 | -43 | -21 |
| perm_seed1731 | 2 | subset_cardinality_refined_o06_size2 | valid | True | False | 0.3492 | 0.5868 | 1.68 | 0.5868 | 0 | -43 | -21 |
| ... | 51 more rows | | | | | | | | | | | |

The failing `perm_seed1730` valid orbit shows a large adapter gain relative to
its event gain and worsens search in all repeats. However `perm_seed1731` also
has a large valid-orbit adapter gain while improving search, so magnitude alone
does not explain the failure. The objective needs both permutation consistency
and magnitude restraint.

## Random Negative Control

| base_instance_id | primary_classification | rows | cpu_down_rows | cpu_up_rows | decisions_down_rows | decisions_up_rows | conflicts_down_rows | conflicts_up_rows | event_state_l2_mean | event_adapter_graph_gate_evidence_mean | warmup_decisions_mean | warmup_conflicts_mean | orbit_audit_rows | valid_orbit_rows | event_positive_orbit_rows | max_adapter_identity_gain_audited | negative_control_signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v100_c600_seed1914 | negative | 9 | 4 | 5 | 0 | 9 | 0 | 9 | 4624 | 4.502 | 180.3 | 158.3 | 0 | 0 | 0 | nan | non_symmetric_search_worsening |
| random_3sat_control_v20_c85_seed1901 | negative | 9 | 4 | 5 | 9 | 0 | 0 | 0 | 33.84 | 0.6931 | 9 | 0 | 180 | 0 | 0 | 0 | non_symmetric_search_change |
| random_3sat_control_v30_c128_seed1902 | negative | 9 | 1 | 7 | 3 | 3 | 3 | 6 | 164 | 2.345 | 15.33 | 14.33 | 0 | 0 | 0 | nan | non_symmetric_search_worsening |
| random_3sat_control_v35_c149_seed1911 | negative | 9 | 5 | 3 | 0 | 9 | 0 | 9 | 155 | 1.792 | 14 | 7 | 0 | 0 | 0 | nan | non_symmetric_search_worsening |
| random_3sat_control_v40_c170_seed1903 | negative | 9 | 6 | 3 | 3 | 6 | 0 | 9 | 68.47 | 0.6931 | 10 | 0 | 0 | 0 | 0 | nan | non_symmetric_search_worsening |
| random_3sat_control_v60_c180_seed1912 | strict_positive | 9 | 7 | 2 | 3 | 0 | 9 | 0 | 162.9 | 1.609 | 19 | 6 | 540 | 0 | 0 | 0 | non_symmetric_strict_positive_perturbation |
| random_3sat_control_v80_c340_seed1913 | negative | 9 | 4 | 5 | 0 | 9 | 0 | 9 | 171.6 | 1.099 | 23 | 2 | 0 | 0 | 0 | nan | non_symmetric_search_worsening |

Random controls show that adapter/runtime changes can be generic perturbations.
The current strict-positive random control is a perturbation baseline, not
symmetry evidence. Non-symmetric controls should therefore constrain adapter
delta unless valid orbit-aligned evidence exists.

## Objective-Level Fixes

| issue | evidence | objective_change | priority |
| --- | --- | --- | --- |
| permutation_non_robust_adapter_alignment | subset base-vs-perm_seed1730 mean adapted_mu_spearman=0.415; perm_seed1730 is search-worse while base improves | add variable-level permutation consistency on adapted mu/rho and adapter delta using metadata permutations | high |
| valid_invalid_orbit_mixing | subset repeat-level event/adaptor maxima are dominated by static_mu_not_collapsed rows; only one refined orbit is event-row-valid per variant | compute reward/identity losses on valid event rows only and report invalid-orbit diagnostics separately | high |
| over_adaptation_magnitude_risk | subset perm_seed1730 valid orbit has event_gain=0.572, adapter_gain=0.78, and search worsens in 3/3 repeats | add adapter delta magnitude regularization or amplification cap, especially when one valid orbit dominates the delta | medium |
| non_symmetric_generic_perturbation | random controls include 1 non-symmetric strict-positive perturbation and 5 majority search-worsening controls | add non-symmetric/no-valid-orbit negative guard that suppresses adapter deltas unless valid orbit-aligned identity evidence exists | high |
| gate_selector_not_ready | mechanism is not stable across permutations or controls; runtime positives include perturbation baselines | keep gate/selector postponed until multiple symmetry families show stable aligned mechanism and controls stay bounded | policy |

## Decision

- Do not proceed to gate/selector from this state.
- Do not expand full runtime to chase surface positives.
- Fix the objective side first: permutation consistency, valid-orbit masking,
  non-symmetric negative guard, and adapter delta magnitude restraint.

## Artifacts

- subset pair alignment: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_subset_pair_alignment_v2.csv`
- subset pair summary: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_subset_pair_summary_v2.csv`
- subset variant summary: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_subset_variant_summary_v2.csv`
- subset orbit contribution: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_subset_orbit_contrib_v2.csv`
- over-adaptation orbits: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_overadaptation_orbits_v2.csv`
- random control summary: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_random_control_summary_v2.csv`
- objective recommendations: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_objective_recommendations_v2.csv`
