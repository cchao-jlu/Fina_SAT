# Adapter Family-Heldout Multi-Seed Audit

This is a representation-only leave-one-family-out adapter audit.
Each heldout family is trained with multiple adapter initialization
seeds on cached event traces from the other families, then evaluated
on the same cached event-state audit set. No solver speedup or runtime
claim is made here.

Bootstrap intervals are over seed-level heldout means with 10000 resamples.
The full-adapter baseline is `runs/analysis/symmetry_adapter_neggate_permcons_vc_w05_event_orbits.csv`.

## Multi-Seed Summary

| heldout_family | seeds | seed_list | heldout_valid_rows | heldout_valid_instances | heldout_gain_mean | heldout_gain_std | heldout_gain_min | heldout_gain_max | heldout_gain_bootstrap_ci_low | heldout_gain_bootstrap_ci_high | positive_gain_seeds | train_gain_mean | heldout_minus_train_gain_mean | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain_mean | heldout_minus_full_bootstrap_ci_low | heldout_minus_full_bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 3 | 1729,1730,1731 | 12 | 12 | 0.8548 | 0.09779 | 0.7534 | 0.9485 | 0.7534 | 0.9485 | 3 | 0.2296 | 0.6252 | 1.151 | -0.2963 | -0.3977 | -0.2025 |

## Seed-Level Summary

| heldout_family | train_seed | train_eval_families | train_valid_families | heldout_eval_instances | heldout_valid_instances | heldout_orbit_rows | train_valid_rows | heldout_valid_rows | train_mean_adapter_gain_valid | heldout_mean_adapter_gain_valid | heldout_minus_train_gain | heldout_mean_adapted_mu_range_valid | heldout_max_adapted_mu_range_valid | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 1729 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.1893 | 0.7534 | 0.5641 | 0.7534 | 0.8885 | 1.151 | -0.3977 |
| vertex_cover_torus | 1730 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.2681 | 0.9485 | 0.6804 | 0.9485 | 1.117 | 1.151 | -0.2025 |
| vertex_cover_torus | 1731 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.2314 | 0.8624 | 0.631 | 0.8624 | 1.002 | 1.151 | -0.2886 |

## Evaluation Family Matrix

| heldout_family | eval_family | adapter_train_split | seeds | valid_rollout_rows | mean_adapter_gain_valid_mean | mean_adapter_gain_valid_std | mean_adapted_mu_range_valid_mean | max_adapted_mu_range_valid_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | complete_coloring | train | 3 | 3 | 0.7477 | 0.1666 | 0.7477 | 0.9136 |
| vertex_cover_torus | dominating_set_hex | train | 3 | 33 | 0.1813 | 0.02823 | 0.1813 | 0.5015 |
| vertex_cover_torus | even_colouring | train | 3 | 42 | 0.06742 | 0.01222 | 0.06742 | 0.449 |
| vertex_cover_torus | php | train | 3 | 3 | 0.7883 | 0.1681 | 0.7883 | 0.9958 |
| vertex_cover_torus | php_exit_all | train | 3 | 6 | 0.2739 | 0.04707 | 0.2739 | 0.6674 |
| vertex_cover_torus | php_exit_single | train | 3 | 12 | 0.1209 | 0.0218 | 0.1209 | 0.5426 |
| vertex_cover_torus | subset_cardinality | train | 3 | 12 | 0.3772 | 0.07632 | 0.3772 | 1.01 |
| vertex_cover_torus | tseitin_complete | train | 3 | 9 | 0.7233 | 0.1025 | 0.7233 | 1.224 |
| vertex_cover_torus | vertex_cover_torus | heldout | 3 | 12 | 0.8548 | 0.09779 | 0.8548 | 1.117 |

## Inputs

- `runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1729_orbits.csv`
- `runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1730_orbits.csv`
- `runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1731_orbits.csv`
