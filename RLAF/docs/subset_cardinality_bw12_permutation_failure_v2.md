# subset_cardinality_bw12 Permutation Failure Diagnosis v2

## Scope

This is an adapter objective / permutation robustness diagnosis. It does not run a full benchmark, does not train a gate/selector, and does not make a speedup claim.

The question is why `subset_cardinality_bw12::perm_seed1730` has strong event signal and adapter separation but worse final decisions/conflicts.

## Variant Summary

| variant | search_direction | repeat_rows | search_worse_rows | decisions_delta_mean | conflicts_delta_mean | valid_event_gain_max | valid_adapter_gain_max | valid_adapter_to_event_ratio | invalid_event_gain_max | invalid_adapter_gain_max | valid_orbit_event_l2_min | valid_orbit_event_l2_max | valid_orbit_delta_mu_min | valid_orbit_delta_mu_max | valid_orbit_rows | invalid_orbit_rows | invalid_rows_static_mu_not_collapsed | objective_proxy_label | objective_proxy_score | objective_permutation_penalty | objective_invalid_orbit_penalty | overadaptation_valid_rows | pair_base_vs_perm_seed1730_search_mismatch_rows | pair_base_vs_perm_seed1730_adapted_mu_spearman | pair_base_vs_perm_seed1730_delta_mu_spearman | pair_base_vs_perm_seed1730_valid_adapter_gain_abs_diff | pair_base_vs_perm_seed1731_search_mismatch_rows | pair_base_vs_perm_seed1731_adapted_mu_spearman | pair_base_vs_perm_seed1731_delta_mu_spearman | pair_base_vs_perm_seed1731_valid_adapter_gain_abs_diff | pair_perm_seed1730_vs_perm_seed1731_search_mismatch_rows | pair_perm_seed1730_vs_perm_seed1731_adapted_mu_spearman | pair_perm_seed1730_vs_perm_seed1731_delta_mu_spearman | pair_perm_seed1730_vs_perm_seed1731_valid_adapter_gain_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | better | 3 | 0 | -55 | -22 | 0.42595 | 0.021885 | 0.051379 | 15.263 | 0.93091 | 52.568 | 52.994 | 0.97811 | 1 | 3 | 24 | 21 | positive | 3.3722 | 0 | 0.20278 | 3 | 27 | 0.41531 | 0.2378 | 0.75772 | 0 | 0.60002 | 0.18809 | 0.56495 | nan | nan | nan | nan |
| perm_seed1730 | worse | 3 | 3 | 13 | 1 | 0.57225 | 0.7796 | 1.3624 | 41.06 | 0.73026 | 44.689 | 45.262 | 0.2204 | 1 | 3 | 24 | 21 | negative | -3.8562 | 1.8597 | 0.18627 | 3 | 27 | 0.41531 | 0.2378 | 0.75772 | nan | nan | nan | nan | 27 | 0.78121 | 0.54352 | 0.19277 |
| perm_seed1731 | better | 3 | 0 | -43 | -21 | 0.34924 | 0.58684 | 1.6803 | 35.813 | 0.71778 | 46.178 | 46.527 | 0.41316 | 1 | 3 | 24 | 21 | positive | 3.1301 | 0 | 0.19212 | 3 | nan | nan | nan | nan | 0 | 0.60002 | 0.18809 | 0.56495 | 27 | 0.78121 | 0.54352 | 0.19277 |

## Pairwise Permutation Alignment

| left_variant | right_variant | orbit_pair_rows | valid_pair_rows | search_direction_mismatch_rows | mean_static_mu_spearman | mean_static_rho_spearman | mean_adapted_mu_spearman | mean_adapted_rho_spearman | mean_delta_mu_spearman | mean_delta_mu_sign_agreement | valid_mean_event_gain_abs_diff | valid_mean_adapter_gain_abs_diff | all_mean_event_gain_abs_diff | all_mean_adapter_gain_abs_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | perm_seed1730 | 27 | 3 | 27 | 0.87096 | 0.62343 | 0.41531 | 0.62343 | 0.2378 | 1 | 0.14629 | 0.75772 | 9.6909 | 0.22813 |
| base | perm_seed1731 | 27 | 3 | 0 | 0.86257 | 0.70404 | 0.60002 | 0.70404 | 0.18809 | 1 | 0.076714 | 0.56495 | 7.4244 | 0.14187 |
| perm_seed1730 | perm_seed1731 | 27 | 3 | 27 | 0.91431 | 0.88475 | 0.78121 | 0.88475 | 0.54352 | 1 | 0.22301 | 0.19277 | 2.5965 | 0.14691 |

## Valid/Invalid Orbit Contribution

| variant | event_row_valid_reason | rows | search_worse_rows | event_identity_gain_mean | event_identity_gain_max | adapter_identity_gain_mean | adapter_identity_gain_max | adapted_mu_range_max | static_mu_range_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | orbit_size_below_min | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| base | static_mu_not_collapsed | 21 | 0 | 5.751 | 15.263 | 0.34538 | 0.93091 | 0.93116 | 0.0019868 |
| base | valid | 3 | 0 | 0.42595 | 0.42595 | 0.021885 | 0.021885 | 0.021885 | 2.9802e-08 |
| perm_seed1730 | orbit_size_below_min | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| perm_seed1730 | static_mu_not_collapsed | 21 | 21 | 11.612 | 41.06 | 0.30835 | 0.73026 | 0.73052 | 0.0019868 |
| perm_seed1730 | valid | 3 | 3 | 0.57225 | 0.57225 | 0.7796 | 0.7796 | 0.7796 | 0 |
| perm_seed1731 | orbit_size_below_min | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| perm_seed1731 | static_mu_not_collapsed | 21 | 0 | 9.3872 | 35.813 | 0.30703 | 0.71778 | 0.71805 | 0.0019868 |
| perm_seed1731 | valid | 3 | 0 | 0.34924 | 0.34924 | 0.58684 | 0.58684 | 0.58684 | 0 |

## Valid Orbit Variable Rows

| variant | repeat_id | original_var | event_l2 | static_mu | adapted_mu | delta_mu | primary_delta_final_decisions | primary_delta_final_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0 | 13 | 52.568 | -0.076823 | 0.90129 | 0.97811 | -55 | -22 |
| base | 0 | 44 | 52.994 | -0.076823 | 0.92318 | 1 | -55 | -22 |
| base | 1 | 13 | 52.568 | -0.076823 | 0.90129 | 0.97811 | -55 | -22 |
| base | 1 | 44 | 52.994 | -0.076823 | 0.92318 | 1 | -55 | -22 |
| base | 2 | 13 | 52.568 | -0.076823 | 0.90129 | 0.97811 | -55 | -22 |
| base | 2 | 44 | 52.994 | -0.076823 | 0.92318 | 1 | -55 | -22 |
| perm_seed1730 | 0 | 13 | 44.689 | -0.076823 | 0.14357 | 0.2204 | 13 | 1 |
| perm_seed1730 | 0 | 44 | 45.262 | -0.076823 | 0.92318 | 1 | 13 | 1 |
| perm_seed1730 | 1 | 13 | 44.689 | -0.076823 | 0.14357 | 0.2204 | 13 | 1 |
| perm_seed1730 | 1 | 44 | 45.262 | -0.076823 | 0.92318 | 1 | 13 | 1 |
| perm_seed1730 | 2 | 13 | 44.689 | -0.076823 | 0.14357 | 0.2204 | 13 | 1 |
| perm_seed1730 | 2 | 44 | 45.262 | -0.076823 | 0.92318 | 1 | 13 | 1 |
| perm_seed1731 | 0 | 13 | 46.178 | -0.076823 | 0.33634 | 0.41316 | -43 | -21 |
| perm_seed1731 | 0 | 44 | 46.527 | -0.076823 | 0.92318 | 1 | -43 | -21 |
| perm_seed1731 | 1 | 13 | 46.178 | -0.076823 | 0.33634 | 0.41316 | -43 | -21 |
| perm_seed1731 | 1 | 44 | 46.527 | -0.076823 | 0.92318 | 1 | -43 | -21 |
| perm_seed1731 | 2 | 13 | 46.178 | -0.076823 | 0.33634 | 0.41316 | -43 | -21 |
| perm_seed1731 | 2 | 44 | 46.527 | -0.076823 | 0.92318 | 1 | -43 | -21 |

## Diagnosis

- This is not an event-missing case: all three variants have valid event-positive rows on the same refined size-2 orbit.
- `perm_seed1730` worsens decisions/conflicts in 3/3 repeats while `base` and `perm_seed1731` improve search counts.
- Pairwise alignment is weakest for `base` vs `perm_seed1730`: adapted-mu Spearman is 0.415 and delta-mu Spearman is 0.238, with search-direction mismatch on all orbit pair rows.
- Invalid rows are still large in raw maxima: `static_mu_not_collapsed` rows dominate event gain, so positive objectives must use valid orbit masks and keep invalid rows diagnostic-only.
- Magnitude alone is insufficient: `perm_seed1731` also has a large valid adapter/event ratio but improves search. The objective needs permutation consistency plus magnitude restraint and non-symmetric/no-valid-orbit guards.

## Objective Implication

`perm_seed1730` should be treated as a hard negative for the adapter objective: valid event evidence is present, but the adapter delta is permutation-non-robust and search-worsening. This supports Objective Fix v1 rather than broader runtime expansion.
