# Adapter Family-Heldout Audit

This is a representation-only leave-one-family-out audit. Each adapter
checkpoint is trained on cached event traces from all event-role
families except one, then evaluated on the same cached event-state
audit set. No solver speedup or runtime claim is made here.

## Leave-One-Family-Out Summary

| heldout_family | train_eval_families | train_valid_families | heldout_eval_instances | heldout_valid_instances | heldout_orbit_rows | train_valid_rows | heldout_valid_rows | train_mean_adapter_gain_valid | heldout_mean_adapter_gain_valid | heldout_minus_train_gain | train_mean_adapted_mu_range_valid | heldout_mean_adapted_mu_range_valid | heldout_minus_train_adapted_mu_range | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.1732 | 0.6872 | 0.514 | 0.1732 | 0.6872 | 0.514 | 0.8591 | -0.1718 |
| dominating_set_hex | 8 | 7 | 9 | 6 | 96 | 87 | 33 | 0.2284 | 0.1327 | -0.09568 | 0.2284 | 0.1327 | -0.09568 | 0.1722 | -0.03946 |
| even_colouring | 8 | 7 | 3 | 3 | 45 | 78 | 42 | 0.2143 | 0.03863 | -0.1756 | 0.2143 | 0.03863 | -0.1756 | 0.06924 | -0.03061 |
| php | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.1913 | 0.8319 | 0.6405 | 0.1913 | 0.8319 | 0.6405 | 0.9272 | -0.09537 |
| php_exit_all | 8 | 7 | 3 | 3 | 6 | 114 | 6 | 0.2251 | 0.2483 | 0.02314 | 0.2251 | 0.2483 | 0.02314 | 0.2713 | -0.02303 |
| php_exit_single | 8 | 7 | 6 | 6 | 18 | 108 | 12 | 0.2034 | 0.1077 | -0.09571 | 0.2034 | 0.1077 | -0.09571 | 0.1359 | -0.02825 |
| subset_cardinality | 8 | 7 | 3 | 3 | 15 | 108 | 12 | 0.23 | 0.4297 | 0.1997 | 0.23 | 0.4297 | 0.1997 | 0.4184 | 0.01123 |
| tseitin_complete | 8 | 7 | 6 | 6 | 9 | 111 | 9 | 0.1514 | 0.5533 | 0.4019 | 0.1514 | 0.5533 | 0.4019 | 0.7239 | -0.1705 |
| vertex_cover_torus | 8 | 8 | 3 | 0 | 3 | 120 | 0 | 0.2481 | nan | nan | 0.2481 | nan | nan | nan | nan |

## Evaluation Family Matrix

| heldout_family | eval_family | adapter_train_split | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | mean_static_mu_range_valid | mean_event_l2_valid | mean_adapted_mu_range_valid | max_adapted_mu_range_valid | mean_adapter_gain_valid | max_adapter_gain_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | complete_coloring | heldout | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.6872 | 0.7198 | 0.6872 | 0.7198 |
| complete_coloring | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1371 | 0.3221 | 0.1371 | 0.3221 |
| complete_coloring | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.04835 | 0.2718 | 0.04835 | 0.2718 |
| complete_coloring | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.7511 | 0.8218 | 0.7511 | 0.8218 |
| complete_coloring | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2024 | 0.4847 | 0.2024 | 0.4847 |
| complete_coloring | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.09694 | 0.321 | 0.09694 | 0.321 |
| complete_coloring | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.337 | 0.7097 | 0.337 | 0.7097 |
| complete_coloring | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.5598 | 0.8647 | 0.5598 | 0.8647 |
| complete_coloring | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| dominating_set_hex | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.7451 | 0.7768 | 0.7451 | 0.7768 |
| dominating_set_hex | dominating_set_hex | heldout | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1327 | 0.3292 | 0.1327 | 0.3292 |
| dominating_set_hex | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05962 | 0.3352 | 0.05962 | 0.3352 |
| dominating_set_hex | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.7991 | 0.8394 | 0.7991 | 0.8394 |
| dominating_set_hex | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.238 | 0.5436 | 0.238 | 0.5436 |
| dominating_set_hex | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1178 | 0.3954 | 0.1178 | 0.3954 |
| dominating_set_hex | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3645 | 0.8071 | 0.3645 | 0.8071 |
| dominating_set_hex | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.6131 | 0.9073 | 0.6131 | 0.9073 |
| dominating_set_hex | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| even_colouring | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.5591 | 0.5819 | 0.5591 | 0.5819 |
| even_colouring | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1193 | 0.2891 | 0.1193 | 0.2891 |
| even_colouring | even_colouring | heldout | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.03863 | 0.2019 | 0.03863 | 0.2019 |
| even_colouring | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.6091 | 0.6621 | 0.6091 | 0.6621 |
| even_colouring | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.1605 | 0.3883 | 0.1605 | 0.3883 |
| even_colouring | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.07484 | 0.2533 | 0.07484 | 0.2533 |
| even_colouring | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.2837 | 0.615 | 0.2837 | 0.615 |
| even_colouring | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.4453 | 0.6925 | 0.4453 | 0.6925 |
| even_colouring | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| php | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.7638 | 0.8001 | 0.7638 | 0.8001 |
| php | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1489 | 0.3666 | 0.1489 | 0.3666 |
| php | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05541 | 0.3135 | 0.05541 | 0.3135 |
| php | php | heldout | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.8319 | 0.8918 | 0.8319 | 0.8918 |
| php | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2299 | 0.5436 | 0.2299 | 0.5436 |
| php | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1119 | 0.3753 | 0.1119 | 0.3753 |
| php | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3855 | 0.8088 | 0.3855 | 0.8088 |
| php | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.6118 | 0.9229 | 0.6118 | 0.9229 |
| php | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| php_exit_all | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.802 | 0.8341 | 0.802 | 0.8341 |
| php_exit_all | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.164 | 0.4001 | 0.164 | 0.4001 |
| php_exit_all | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.06467 | 0.3753 | 0.06467 | 0.3753 |
| php_exit_all | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.8691 | 0.921 | 0.8691 | 0.921 |
| php_exit_all | php_exit_all | heldout | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2483 | 0.5739 | 0.2483 | 0.5739 |
| php_exit_all | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1244 | 0.4147 | 0.1244 | 0.4147 |
| php_exit_all | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3979 | 0.8611 | 0.3979 | 0.8611 |
| php_exit_all | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.6951 | 1.044 | 0.6951 | 1.044 |
| php_exit_all | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| php_exit_single | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.7039 | 0.7389 | 0.7039 | 0.7389 |
| php_exit_single | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1375 | 0.3314 | 0.1375 | 0.3314 |
| php_exit_single | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05235 | 0.2923 | 0.05235 | 0.2923 |
| php_exit_single | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.77 | 0.8349 | 0.77 | 0.8349 |
| php_exit_single | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2129 | 0.5003 | 0.2129 | 0.5003 |
| php_exit_single | php_exit_single | heldout | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1077 | 0.3555 | 0.1077 | 0.3555 |
| php_exit_single | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3592 | 0.7603 | 0.3592 | 0.7603 |
| php_exit_single | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.5798 | 0.8798 | 0.5798 | 0.8798 |
| php_exit_single | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| subset_cardinality | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.8956 | 0.937 | 0.8956 | 0.937 |
| subset_cardinality | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.1843 | 0.4623 | 0.1843 | 0.4623 |
| subset_cardinality | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.06977 | 0.4109 | 0.06977 | 0.4109 |
| subset_cardinality | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.964 | 1.041 | 0.964 | 1.041 |
| subset_cardinality | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2782 | 0.6567 | 0.2782 | 0.6567 |
| subset_cardinality | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1332 | 0.4532 | 0.1332 | 0.4532 |
| subset_cardinality | subset_cardinality | heldout | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.4297 | 0.8764 | 0.4297 | 0.8764 |
| subset_cardinality | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.7755 | 1.169 | 0.7755 | 1.169 |
| subset_cardinality | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| tseitin_complete | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.6548 | 0.6675 | 0.6548 | 0.6675 |
| tseitin_complete | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.128 | 0.3456 | 0.128 | 0.3456 |
| tseitin_complete | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.05018 | 0.2793 | 0.05018 | 0.2793 |
| tseitin_complete | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.7138 | 0.7508 | 0.7138 | 0.7508 |
| tseitin_complete | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.1954 | 0.459 | 0.1954 | 0.459 |
| tseitin_complete | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.09774 | 0.3224 | 0.09774 | 0.3224 |
| tseitin_complete | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.3357 | 0.7219 | 0.3357 | 0.7219 |
| tseitin_complete | tseitin_complete | heldout | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.5533 | 0.8468 | 0.5533 | 0.8468 |
| tseitin_complete | vertex_cover_torus | train | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| vertex_cover_torus | complete_coloring | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.555 | 0.894 | 0.9341 | 0.894 | 0.9341 |
| vertex_cover_torus | dominating_set_hex | train | 9 | 96 | 33 | 33 | 0 | 1.05e-08 | 1.132 | 0.178 | 0.4318 | 0.178 | 0.4318 |
| vertex_cover_torus | even_colouring | train | 3 | 45 | 42 | 42 | 0 | 2.936e-08 | 0.1625 | 0.06857 | 0.3885 | 0.06857 | 0.3885 |
| vertex_cover_torus | php | train | 6 | 6 | 3 | 3 | 0 | 2.235e-08 | 9.493 | 0.9665 | 1.028 | 0.9665 | 1.028 |
| vertex_cover_torus | php_exit_all | train | 3 | 6 | 6 | 6 | 0 | 2.732e-08 | 0.5945 | 0.2786 | 0.6459 | 0.2786 | 0.6459 |
| vertex_cover_torus | php_exit_single | train | 6 | 18 | 12 | 12 | 0 | 2.359e-08 | 0.4408 | 0.1366 | 0.4558 | 0.1366 | 0.4558 |
| vertex_cover_torus | subset_cardinality | train | 3 | 15 | 12 | 12 | 0 | 1.925e-08 | 0.9573 | 0.4564 | 0.9606 | 0.4564 | 0.9606 |
| vertex_cover_torus | tseitin_complete | train | 6 | 9 | 9 | 9 | 0 | 3.601e-08 | 0.6254 | 0.7383 | 1.106 | 0.7382 | 1.106 |
| vertex_cover_torus | vertex_cover_torus | heldout | 3 | 3 | 0 | 0 | 0 | nan | nan | nan | nan | nan | nan |

## Inputs

- `runs/analysis/symmetry_adapter_heldout_complete_coloring_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_dominating_set_hex_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_even_colouring_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_php_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_php_exit_all_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_php_exit_single_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_subset_cardinality_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_tseitin_complete_orbits.csv`
- `runs/analysis/symmetry_adapter_heldout_vertex_cover_torus_orbits.csv`
