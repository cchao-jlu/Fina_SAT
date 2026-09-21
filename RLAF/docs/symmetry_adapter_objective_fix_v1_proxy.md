# Symmetry Adapter Objective Fix v1 Proxy

This is an offline objective proxy over the frozen v2 diagnosis CSVs. It is not a solver speedup claim, does not expand the full runtime benchmark, and does not train a gate/selector.

Proxy formula:

```text
objective_score = search_delta_reward
  - permutation_inconsistency_penalty
  - invalid_orbit_identity_penalty
  - non_symmetric_perturbation_penalty
  - adapter_delta_magnitude_penalty
```

Positive search-count deltas are penalized and negative deltas are rewarded. Non-symmetric controls receive no positive search reward; their search changes are treated as perturbation risk.

## Summary

| case_type | rows | positive_rows | mixed_rows | negative_rows | objective_score_mean | search_delta_reward_mean | penalty_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| non_symmetric_control | 7 | 0 | 0 | 7 | -3.285 | 0 | 3.285 |
| symmetry_calibration | 1 | 1 | 0 | 0 | 0.6454 | 0.8047 | 0.1594 |
| symmetry_targeted | 1 | 1 | 0 | 0 | 0.8973 | 0.9962 | 0.0989 |
| symmetry_variant | 3 | 2 | 0 | 1 | 0.882 | 1.784 | 0.9019 |

## Named Checks

| case_id | case_type | proxy_label | objective_score | search_delta_reward | permutation_inconsistency_penalty | invalid_orbit_identity_penalty | non_symmetric_perturbation_penalty | adapter_delta_magnitude_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k5_color4 | symmetry_calibration | positive | 0.6454 | 0.8047 | 0 | 0 | 0 | 0.1594 |
| dominating_set_hex_3x6_s4 | symmetry_targeted | positive | 0.8973 | 0.9962 | 0 | 0 | 0 | 0.0989 |
| subset_cardinality_bw12::base | symmetry_variant | positive | 3.372 | 3.58 | 0 | 0.2028 | 0 | 0.005412 |
| subset_cardinality_bw12::perm_seed1730 | symmetry_variant | negative | -3.856 | -1.666 | 1.86 | 0.1863 | 0 | 0.1441 |
| subset_cardinality_bw12::perm_seed1731 | symmetry_variant | positive | 3.13 | 3.438 | 0 | 0.1921 | 0 | 0.1154 |

## Subset Permutation Split

| case_id | case_type | proxy_label | objective_score | search_delta_reward | permutation_inconsistency_penalty | invalid_orbit_identity_penalty | non_symmetric_perturbation_penalty | adapter_delta_magnitude_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality_bw12::base | symmetry_variant | positive | 3.372 | 3.58 | 0 | 0.2028 | 0 | 0.005412 |
| subset_cardinality_bw12::perm_seed1730 | symmetry_variant | negative | -3.856 | -1.666 | 1.86 | 0.1863 | 0 | 0.1441 |
| subset_cardinality_bw12::perm_seed1731 | symmetry_variant | positive | 3.13 | 3.438 | 0 | 0.1921 | 0 | 0.1154 |

## Random Controls

| case_id | proxy_label | objective_score | non_symmetric_perturbation_penalty | notes |
| --- | --- | --- | --- | --- |
| random_3sat_control_v100_c600_seed1914 | negative | -3.766 | 3.766 | non_symmetric_search_worsening |
| random_3sat_control_v20_c85_seed1901 | negative | -2.533 | 2.533 | non_symmetric_search_change |
| random_3sat_control_v30_c128_seed1902 | negative | -3.099 | 3.099 | non_symmetric_search_worsening |
| random_3sat_control_v35_c149_seed1911 | negative | -3.258 | 3.258 | non_symmetric_search_worsening |
| random_3sat_control_v40_c170_seed1903 | negative | -3.136 | 3.136 | non_symmetric_search_worsening |
| random_3sat_control_v60_c180_seed1912 | negative | -3.932 | 3.932 | non_symmetric_strict_positive_perturbation |
| random_3sat_control_v80_c340_seed1913 | negative | -3.273 | 3.273 | non_symmetric_search_worsening |

## Interpretation

- `subset_cardinality_bw12::perm_seed1730` is penalized because it is the direction-outlier permutation variant: valid orbit evidence exists, but final decisions/conflicts worsen and pairwise permutation consistency is poor.
- `subset_cardinality_bw12::base` and `subset_cardinality_bw12::perm_seed1731` remain positive despite invalid-orbit warnings because their search-count deltas improve and they are not the direction outlier.
- `dominating_set_hex_3x6_s4` remains positive/mixed-aligned on the proxy: conflicts improve and valid event-orbit evidence exists, while CPU is intentionally ignored.
- Random controls are all negative under the non-symmetric perturbation guard, including the strict-positive runtime perturbation control.

Next step remains default-off loss implementation plus unit/smoke verification, not full runtime or gate training.
