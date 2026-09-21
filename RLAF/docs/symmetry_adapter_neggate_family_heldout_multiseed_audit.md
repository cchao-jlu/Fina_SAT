# Adapter Family-Heldout Multi-Seed Audit

This is a representation-only leave-one-family-out adapter audit.
Each heldout family is trained with multiple adapter initialization
seeds on cached event traces from the other families, then evaluated
on the same cached event-state audit set. No solver speedup or runtime
claim is made here.

Bootstrap intervals are over seed-level heldout means with 10000 resamples.
The full-adapter baseline is `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_event_orbits.csv`.

## Multi-Seed Summary

| heldout_family | seeds | seed_list | heldout_valid_rows | heldout_valid_instances | heldout_gain_mean | heldout_gain_std | heldout_gain_min | heldout_gain_max | heldout_gain_bootstrap_ci_low | heldout_gain_bootstrap_ci_high | positive_gain_seeds | train_gain_mean | heldout_minus_train_gain_mean | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain_mean | heldout_minus_full_bootstrap_ci_low | heldout_minus_full_bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1729,1730,1731 | 3 | 3 | 0.9881 | 0.08348 | 0.8921 | 1.043 | 0.8921 | 1.043 | 3 | 0.2535 | 0.7346 | 1.081 | -0.09239 | -0.1885 | -0.03749 |
| dominating_set_hex | 3 | 1729,1730,1731 | 33 | 6 | 0.1551 | 0.02829 | 0.1368 | 0.1877 | 0.1368 | 0.1877 | 3 | 0.2727 | -0.1175 | 0.2188 | -0.06371 | -0.08199 | -0.03112 |
| even_colouring | 3 | 1729,1730,1731 | 42 | 3 | 0.05783 | 0.003952 | 0.05331 | 0.0606 | 0.05331 | 0.0606 | 3 | 0.3168 | -0.259 | 0.08404 | -0.02621 | -0.03074 | -0.02344 |
| php | 3 | 1729,1730,1731 | 3 | 3 | 1.024 | 0.07269 | 0.9406 | 1.067 | 0.9406 | 1.067 | 3 | 0.2483 | 0.7761 | 1.169 | -0.1441 | -0.2281 | -0.1016 |
| php_exit_all | 3 | 1729,1730,1731 | 6 | 3 | 0.2725 | 0.01338 | 0.2621 | 0.2876 | 0.2621 | 0.2876 | 3 | 0.2456 | 0.02697 | 0.3552 | -0.08263 | -0.09305 | -0.06754 |
| php_exit_single | 3 | 1729,1730,1731 | 12 | 6 | 0.1173 | 0.01111 | 0.1063 | 0.1286 | 0.1063 | 0.1286 | 3 | 0.2552 | -0.1379 | 0.1511 | -0.03383 | -0.0448 | -0.02258 |
| subset_cardinality | 3 | 1729,1730,1731 | 12 | 3 | 0.555 | 0.04365 | 0.5088 | 0.5956 | 0.5088 | 0.5956 | 3 | 0.281 | 0.2739 | 0.5219 | 0.03311 | -0.01303 | 0.07375 |
| tseitin_complete | 3 | 1729,1730,1731 | 9 | 6 | 0.7308 | 0.06223 | 0.685 | 0.8016 | 0.685 | 0.8016 | 3 | 0.2046 | 0.5262 | 0.8911 | -0.1604 | -0.2061 | -0.08949 |
| vertex_cover_torus | 3 | 1729,1730,1731 | 0 | 0 | nan | nan | nan | nan | nan | nan | 0 | 0.2623 | nan | nan | nan | nan | nan |

## Seed-Level Summary

| heldout_family | train_seed | train_eval_families | train_valid_families | heldout_eval_instances | heldout_valid_instances | heldout_orbit_rows | train_valid_rows | heldout_valid_rows | train_mean_adapter_gain_valid | heldout_mean_adapter_gain_valid | heldout_minus_train_gain | heldout_mean_adapted_mu_range_valid | heldout_max_adapted_mu_range_valid | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 1729 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2656 | 1.029 | 0.7637 | 1.029 | 1.066 | 1.081 | -0.05122 |
| complete_coloring | 1730 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2671 | 1.043 | 0.776 | 1.043 | 1.097 | 1.081 | -0.03749 |
| complete_coloring | 1731 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2278 | 0.8921 | 0.6643 | 0.8921 | 0.9174 | 1.081 | -0.1885 |
| dominating_set_hex | 1729 | 8 | 7 | 9 | 6 | 96 | 87 | 33 | 0.248 | 0.1408 | -0.1072 | 0.1408 | 0.3521 | 0.2188 | -0.07802 |
| dominating_set_hex | 1730 | 8 | 7 | 9 | 6 | 96 | 87 | 33 | 0.314 | 0.1877 | -0.1263 | 0.1877 | 0.4571 | 0.2188 | -0.03112 |
| dominating_set_hex | 1731 | 8 | 7 | 9 | 6 | 96 | 87 | 33 | 0.2559 | 0.1368 | -0.1191 | 0.1368 | 0.3443 | 0.2188 | -0.08199 |
| even_colouring | 1729 | 8 | 7 | 3 | 3 | 45 | 78 | 42 | 0.3206 | 0.05959 | -0.261 | 0.05959 | 0.3153 | 0.08404 | -0.02445 |
| even_colouring | 1730 | 8 | 7 | 3 | 3 | 45 | 78 | 42 | 0.3304 | 0.0606 | -0.2698 | 0.0606 | 0.3126 | 0.08404 | -0.02344 |
| even_colouring | 1731 | 8 | 7 | 3 | 3 | 45 | 78 | 42 | 0.2995 | 0.05331 | -0.2462 | 0.05331 | 0.2851 | 0.08404 | -0.03074 |
| php | 1729 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2642 | 1.066 | 0.8017 | 1.066 | 1.154 | 1.169 | -0.1028 |
| php | 1730 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2526 | 1.067 | 0.8145 | 1.067 | 1.151 | 1.169 | -0.1016 |
| php | 1731 | 8 | 7 | 6 | 3 | 6 | 117 | 3 | 0.2283 | 0.9406 | 0.7123 | 0.9406 | 1.023 | 1.169 | -0.2281 |
| php_exit_all | 1729 | 8 | 7 | 3 | 3 | 6 | 114 | 6 | 0.2437 | 0.2679 | 0.02422 | 0.2679 | 0.6385 | 0.3552 | -0.08729 |
| php_exit_all | 1730 | 8 | 7 | 3 | 3 | 6 | 114 | 6 | 0.2293 | 0.2621 | 0.03283 | 0.2621 | 0.6102 | 0.3552 | -0.09305 |
| php_exit_all | 1731 | 8 | 7 | 3 | 3 | 6 | 114 | 6 | 0.2638 | 0.2876 | 0.02384 | 0.2876 | 0.7192 | 0.3552 | -0.06754 |
| php_exit_single | 1729 | 8 | 7 | 6 | 6 | 18 | 108 | 12 | 0.2748 | 0.1286 | -0.1462 | 0.1286 | 0.4927 | 0.1511 | -0.02258 |
| php_exit_single | 1730 | 8 | 7 | 6 | 6 | 18 | 108 | 12 | 0.259 | 0.117 | -0.1419 | 0.117 | 0.4463 | 0.1511 | -0.03412 |
| php_exit_single | 1731 | 8 | 7 | 6 | 6 | 18 | 108 | 12 | 0.2319 | 0.1063 | -0.1256 | 0.1063 | 0.4081 | 0.1511 | -0.0448 |
| subset_cardinality | 1729 | 8 | 7 | 3 | 3 | 15 | 108 | 12 | 0.2623 | 0.5088 | 0.2465 | 0.5088 | 1.063 | 0.5219 | -0.01303 |
| subset_cardinality | 1730 | 8 | 7 | 3 | 3 | 15 | 108 | 12 | 0.3006 | 0.5956 | 0.295 | 0.5956 | 1.238 | 0.5219 | 0.07375 |
| subset_cardinality | 1731 | 8 | 7 | 3 | 3 | 15 | 108 | 12 | 0.2802 | 0.5605 | 0.2803 | 0.5605 | 1.15 | 0.5219 | 0.03862 |
| tseitin_complete | 1729 | 8 | 7 | 6 | 6 | 9 | 111 | 9 | 0.1875 | 0.685 | 0.4975 | 0.685 | 1.037 | 0.8911 | -0.2061 |
| tseitin_complete | 1730 | 8 | 7 | 6 | 6 | 9 | 111 | 9 | 0.2323 | 0.8016 | 0.5693 | 0.8016 | 1.197 | 0.8911 | -0.08949 |
| tseitin_complete | 1731 | 8 | 7 | 6 | 6 | 9 | 111 | 9 | 0.1939 | 0.7057 | 0.5118 | 0.7057 | 1.064 | 0.8911 | -0.1854 |
| vertex_cover_torus | 1729 | 8 | 8 | 3 | 0 | 3 | 120 | 0 | 0.2492 | nan | nan | nan | nan | nan | nan |
| vertex_cover_torus | 1730 | 8 | 8 | 3 | 0 | 3 | 120 | 0 | 0.2761 | nan | nan | nan | nan | nan | nan |
| vertex_cover_torus | 1731 | 8 | 8 | 3 | 0 | 3 | 120 | 0 | 0.2616 | nan | nan | nan | nan | nan | nan |

## Evaluation Family Matrix

| heldout_family | eval_family | adapter_train_split | seeds | valid_rollout_rows | mean_adapter_gain_valid_mean | mean_adapter_gain_valid_std | mean_adapted_mu_range_valid_mean | max_adapted_mu_range_valid_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | complete_coloring | heldout | 3 | 3 | 0.9881 | 0.08348 | 0.9881 | 1.097 |
| complete_coloring | dominating_set_hex | train | 3 | 33 | 0.2031 | 0.01531 | 0.2031 | 0.5258 |
| complete_coloring | even_colouring | train | 3 | 42 | 0.07267 | 0.008645 | 0.07267 | 0.4355 |
| complete_coloring | php | train | 3 | 3 | 1.056 | 0.1018 | 1.056 | 1.223 |
| complete_coloring | php_exit_all | train | 3 | 6 | 0.3188 | 0.02376 | 0.3188 | 0.8029 |
| complete_coloring | php_exit_single | train | 3 | 12 | 0.133 | 0.01122 | 0.133 | 0.5445 |
| complete_coloring | subset_cardinality | train | 3 | 12 | 0.4862 | 0.03107 | 0.4862 | 1.132 |
| complete_coloring | tseitin_complete | train | 3 | 9 | 0.8216 | 0.09282 | 0.8216 | 1.309 |
| complete_coloring | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| dominating_set_hex | complete_coloring | train | 3 | 3 | 0.8962 | 0.1065 | 0.8962 | 1.066 |
| dominating_set_hex | dominating_set_hex | heldout | 3 | 33 | 0.1551 | 0.02829 | 0.1551 | 0.4571 |
| dominating_set_hex | even_colouring | train | 3 | 42 | 0.06996 | 0.01305 | 0.06996 | 0.4734 |
| dominating_set_hex | php | train | 3 | 3 | 0.9638 | 0.1093 | 0.9638 | 1.134 |
| dominating_set_hex | php_exit_all | train | 3 | 6 | 0.2893 | 0.0423 | 0.2893 | 0.7536 |
| dominating_set_hex | php_exit_single | train | 3 | 12 | 0.1254 | 0.02003 | 0.1254 | 0.563 |
| dominating_set_hex | subset_cardinality | train | 3 | 12 | 0.4441 | 0.04244 | 0.4441 | 1.088 |
| dominating_set_hex | tseitin_complete | train | 3 | 9 | 0.7369 | 0.1044 | 0.7369 | 1.238 |
| dominating_set_hex | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| even_colouring | complete_coloring | train | 3 | 3 | 0.8513 | 0.03493 | 0.8513 | 0.933 |
| even_colouring | dominating_set_hex | train | 3 | 33 | 0.1751 | 0.01019 | 0.1751 | 0.4806 |
| even_colouring | even_colouring | heldout | 3 | 42 | 0.05783 | 0.003952 | 0.05783 | 0.3153 |
| even_colouring | php | train | 3 | 3 | 0.9272 | 0.03071 | 0.9272 | 1.048 |
| even_colouring | php_exit_all | train | 3 | 6 | 0.2543 | 0.01501 | 0.2543 | 0.6452 |
| even_colouring | php_exit_single | train | 3 | 12 | 0.1058 | 0.006746 | 0.1058 | 0.4306 |
| even_colouring | subset_cardinality | train | 3 | 12 | 0.4002 | 0.01233 | 0.4002 | 0.9844 |
| even_colouring | tseitin_complete | train | 3 | 9 | 0.6671 | 0.05445 | 0.6671 | 1.072 |
| even_colouring | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| php | complete_coloring | train | 3 | 3 | 0.9647 | 0.0649 | 0.9647 | 1.052 |
| php | dominating_set_hex | train | 3 | 33 | 0.2006 | 0.01569 | 0.2006 | 0.5234 |
| php | even_colouring | train | 3 | 42 | 0.07261 | 0.007796 | 0.07261 | 0.4502 |
| php | php | heldout | 3 | 3 | 1.024 | 0.07269 | 1.024 | 1.154 |
| php | php_exit_all | train | 3 | 6 | 0.3137 | 0.0238 | 0.3137 | 0.7829 |
| php | php_exit_single | train | 3 | 12 | 0.1331 | 0.01139 | 0.1331 | 0.5501 |
| php | subset_cardinality | train | 3 | 12 | 0.4794 | 0.02199 | 0.4794 | 1.102 |
| php | tseitin_complete | train | 3 | 9 | 0.8066 | 0.07059 | 0.8066 | 1.291 |
| php | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| php_exit_all | complete_coloring | train | 3 | 3 | 0.9626 | 0.1579 | 0.9626 | 1.188 |
| php_exit_all | dominating_set_hex | train | 3 | 33 | 0.1855 | 0.0153 | 0.1855 | 0.5961 |
| php_exit_all | even_colouring | train | 3 | 42 | 0.06303 | 0.001981 | 0.06303 | 0.3951 |
| php_exit_all | php | train | 3 | 3 | 1.032 | 0.1359 | 1.032 | 1.21 |
| php_exit_all | php_exit_all | heldout | 3 | 6 | 0.2725 | 0.01338 | 0.2725 | 0.7192 |
| php_exit_all | php_exit_single | train | 3 | 12 | 0.1175 | 0.006088 | 0.1175 | 0.4715 |
| php_exit_all | subset_cardinality | train | 3 | 12 | 0.4483 | 0.02088 | 0.4483 | 1.05 |
| php_exit_all | tseitin_complete | train | 3 | 9 | 0.7167 | 0.04466 | 0.7167 | 1.108 |
| php_exit_all | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| php_exit_single | complete_coloring | train | 3 | 3 | 0.8703 | 0.07212 | 0.8703 | 0.9554 |
| php_exit_single | dominating_set_hex | train | 3 | 33 | 0.1818 | 0.01664 | 0.1818 | 0.495 |
| php_exit_single | even_colouring | train | 3 | 42 | 0.06443 | 0.00671 | 0.06443 | 0.3971 |
| php_exit_single | php | train | 3 | 3 | 0.9271 | 0.08312 | 0.9271 | 1.065 |
| php_exit_single | php_exit_all | train | 3 | 6 | 0.2814 | 0.02272 | 0.2814 | 0.7083 |
| php_exit_single | php_exit_single | heldout | 3 | 12 | 0.1173 | 0.01111 | 0.1173 | 0.4927 |
| php_exit_single | subset_cardinality | train | 3 | 12 | 0.4279 | 0.0319 | 0.4279 | 1.012 |
| php_exit_single | tseitin_complete | train | 3 | 9 | 0.7379 | 0.07262 | 0.7379 | 1.209 |
| php_exit_single | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| subset_cardinality | complete_coloring | train | 3 | 3 | 1.071 | 0.0684 | 1.071 | 1.198 |
| subset_cardinality | dominating_set_hex | train | 3 | 33 | 0.2283 | 0.01999 | 0.2283 | 0.6113 |
| subset_cardinality | even_colouring | train | 3 | 42 | 0.08233 | 0.003746 | 0.08233 | 0.5075 |
| subset_cardinality | php | train | 3 | 3 | 1.143 | 0.07534 | 1.143 | 1.355 |
| subset_cardinality | php_exit_all | train | 3 | 6 | 0.3463 | 0.01747 | 0.3463 | 0.8713 |
| subset_cardinality | php_exit_single | train | 3 | 12 | 0.1462 | 0.009878 | 0.1462 | 0.5887 |
| subset_cardinality | subset_cardinality | heldout | 3 | 12 | 0.555 | 0.04365 | 0.555 | 1.238 |
| subset_cardinality | tseitin_complete | train | 3 | 9 | 0.9875 | 0.07658 | 0.9875 | 1.618 |
| subset_cardinality | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| tseitin_complete | complete_coloring | train | 3 | 3 | 0.9036 | 0.09046 | 0.9036 | 1.04 |
| tseitin_complete | dominating_set_hex | train | 3 | 33 | 0.1818 | 0.0232 | 0.1818 | 0.5655 |
| tseitin_complete | even_colouring | train | 3 | 42 | 0.06372 | 0.009059 | 0.06372 | 0.4162 |
| tseitin_complete | php | train | 3 | 3 | 0.9672 | 0.09105 | 0.9672 | 1.148 |
| tseitin_complete | php_exit_all | train | 3 | 6 | 0.2781 | 0.04137 | 0.2781 | 0.7609 |
| tseitin_complete | php_exit_single | train | 3 | 12 | 0.116 | 0.01981 | 0.116 | 0.5243 |
| tseitin_complete | subset_cardinality | train | 3 | 12 | 0.4467 | 0.04372 | 0.4467 | 1.123 |
| tseitin_complete | tseitin_complete | heldout | 3 | 9 | 0.7308 | 0.06223 | 0.7308 | 1.197 |
| tseitin_complete | vertex_cover_torus | train | 3 | 0 | nan | nan | nan | nan |
| vertex_cover_torus | complete_coloring | train | 3 | 3 | 0.9351 | 0.03426 | 0.9351 | 0.9986 |
| vertex_cover_torus | dominating_set_hex | train | 3 | 33 | 0.1946 | 0.01533 | 0.1946 | 0.5088 |
| vertex_cover_torus | even_colouring | train | 3 | 42 | 0.07337 | 0.007649 | 0.07337 | 0.4592 |
| vertex_cover_torus | php | train | 3 | 3 | 0.9963 | 0.05211 | 0.9963 | 1.117 |
| vertex_cover_torus | php_exit_all | train | 3 | 6 | 0.3088 | 0.0189 | 0.3088 | 0.7379 |
| vertex_cover_torus | php_exit_single | train | 3 | 12 | 0.1321 | 0.0115 | 0.1321 | 0.5496 |
| vertex_cover_torus | subset_cardinality | train | 3 | 12 | 0.466 | 0.02435 | 0.466 | 1.045 |
| vertex_cover_torus | tseitin_complete | train | 3 | 9 | 0.7944 | 0.05399 | 0.7944 | 1.253 |
| vertex_cover_torus | vertex_cover_torus | heldout | 3 | 0 | nan | nan | nan | nan |

## Inputs

- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_complete_coloring_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_complete_coloring_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_complete_coloring_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_dominating_set_hex_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_dominating_set_hex_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_dominating_set_hex_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_even_colouring_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_even_colouring_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_even_colouring_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_all_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_all_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_all_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_single_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_single_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_php_exit_single_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_subset_cardinality_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_subset_cardinality_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_subset_cardinality_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_tseitin_complete_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_tseitin_complete_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_tseitin_complete_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_vertex_cover_torus_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_vertex_cover_torus_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_neggate_heldout_vertex_cover_torus_seed1731_orbits.csv`
