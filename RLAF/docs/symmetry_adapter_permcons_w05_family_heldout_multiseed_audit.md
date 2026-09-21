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
| complete_coloring | 3 | 1729,1730,1731 | 3 | 3 | 0.9719 | 0.1183 | 0.8479 | 1.083 | 0.8479 | 1.083 | 3 | 0.3803 | 0.5917 | 0.9097 | 0.06222 | -0.06183 | 0.1737 |
| dominating_set_hex | 3 | 1729,1730,1731 | 33 | 6 | 0.2436 | 0.02932 | 0.2097 | 0.2607 | 0.2097 | 0.2607 | 3 | 0.4023 | -0.1588 | 0.2273 | 0.0163 | -0.01755 | 0.03341 |
| even_colouring | 3 | 1729,1730,1731 | 42 | 3 | 0.04838 | 0.001603 | 0.04697 | 0.05012 | 0.04697 | 0.05012 | 3 | 0.3951 | -0.3467 | 0.07291 | -0.02453 | -0.02595 | -0.02279 |
| php | 3 | 1729,1730,1731 | 3 | 3 | 0.8442 | 0.1357 | 0.6994 | 0.9684 | 0.6994 | 0.9684 | 3 | 0.3434 | 0.5009 | 0.951 | -0.1068 | -0.2516 | 0.01734 |
| php_exit_all | 3 | 1729,1730,1731 | 6 | 3 | 0.384 | 0.01839 | 0.3629 | 0.3969 | 0.3629 | 0.3969 | 3 | 0.3854 | -0.001397 | 0.3232 | 0.06078 | 0.03973 | 0.07372 |
| php_exit_single | 3 | 1729,1730,1731 | 12 | 6 | 0.1639 | 0.02457 | 0.1383 | 0.1872 | 0.1383 | 0.1872 | 3 | 0.4141 | -0.2502 | 0.1399 | 0.02401 | -0.001626 | 0.04736 |
| subset_cardinality | 3 | 1729,1730,1731 | 12 | 3 | 0.5483 | 0.02376 | 0.521 | 0.5639 | 0.521 | 0.5639 | 3 | 0.3607 | 0.1876 | 0.4718 | 0.07649 | 0.04914 | 0.09203 |
| tseitin_complete | 3 | 1729,1730,1731 | 9 | 6 | 0.648 | 0.07729 | 0.6004 | 0.7371 | 0.6004 | 0.7371 | 3 | 0.3341 | 0.3138 | 0.7741 | -0.1261 | -0.1737 | -0.03695 |
| vertex_cover_torus | 3 | 1729,1730,1731 | 12 | 12 | 0.8548 | 0.09779 | 0.7534 | 0.9485 | 0.7534 | 0.9485 | 3 | 0.2296 | 0.6252 | 1.151 | -0.2963 | -0.3977 | -0.2025 |

## Seed-Level Summary

| heldout_family | train_seed | train_eval_families | train_valid_families | heldout_eval_instances | heldout_valid_instances | heldout_orbit_rows | train_valid_rows | heldout_valid_rows | train_mean_adapter_gain_valid | heldout_mean_adapter_gain_valid | heldout_minus_train_gain | heldout_mean_adapted_mu_range_valid | heldout_max_adapted_mu_range_valid | full_adapter_mean_gain_for_heldout_family | heldout_minus_full_adapter_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 1729 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.4025 | 0.9845 | 0.582 | 0.9845 | 1.022 | 0.9097 | 0.07481 |
| complete_coloring | 1730 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.3889 | 0.8479 | 0.459 | 0.8479 | 0.8924 | 0.9097 | -0.06183 |
| complete_coloring | 1731 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.3494 | 1.083 | 0.734 | 1.083 | 1.117 | 0.9097 | 0.1737 |
| dominating_set_hex | 1729 | 8 | 8 | 9 | 6 | 96 | 99 | 33 | 0.3775 | 0.2097 | -0.1678 | 0.2097 | 0.5852 | 0.2273 | -0.01755 |
| dominating_set_hex | 1730 | 8 | 8 | 9 | 6 | 96 | 99 | 33 | 0.4188 | 0.2603 | -0.1585 | 0.2603 | 0.6871 | 0.2273 | 0.03304 |
| dominating_set_hex | 1731 | 8 | 8 | 9 | 6 | 96 | 99 | 33 | 0.4107 | 0.2607 | -0.15 | 0.2607 | 0.6964 | 0.2273 | 0.03341 |
| even_colouring | 1729 | 8 | 8 | 3 | 3 | 45 | 90 | 42 | 0.3961 | 0.04697 | -0.3491 | 0.04697 | 0.2362 | 0.07291 | -0.02595 |
| even_colouring | 1730 | 8 | 8 | 3 | 3 | 45 | 90 | 42 | 0.3881 | 0.05012 | -0.338 | 0.05012 | 0.2545 | 0.07291 | -0.02279 |
| even_colouring | 1731 | 8 | 8 | 3 | 3 | 45 | 90 | 42 | 0.401 | 0.04806 | -0.3529 | 0.04806 | 0.2402 | 0.07291 | -0.02485 |
| php | 1729 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.3426 | 0.9684 | 0.6258 | 0.9684 | 1.07 | 0.951 | 0.01734 |
| php | 1730 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.3575 | 0.8649 | 0.5074 | 0.8649 | 0.9711 | 0.951 | -0.08611 |
| php | 1731 | 8 | 8 | 6 | 3 | 6 | 129 | 3 | 0.3301 | 0.6994 | 0.3693 | 0.6994 | 0.8053 | 0.951 | -0.2516 |
| php_exit_all | 1729 | 8 | 8 | 3 | 3 | 6 | 126 | 6 | 0.3758 | 0.3921 | 0.01622 | 0.3921 | 0.9647 | 0.3232 | 0.06888 |
| php_exit_all | 1730 | 8 | 8 | 3 | 3 | 6 | 126 | 6 | 0.3863 | 0.3969 | 0.0106 | 0.3969 | 0.9585 | 0.3232 | 0.07372 |
| php_exit_all | 1731 | 8 | 8 | 3 | 3 | 6 | 126 | 6 | 0.3939 | 0.3629 | -0.03101 | 0.3629 | 0.907 | 0.3232 | 0.03973 |
| php_exit_single | 1729 | 8 | 8 | 6 | 6 | 18 | 120 | 12 | 0.3911 | 0.1383 | -0.2529 | 0.1383 | 0.5301 | 0.1399 | -0.001626 |
| php_exit_single | 1730 | 8 | 8 | 6 | 6 | 18 | 120 | 12 | 0.437 | 0.1872 | -0.2498 | 0.1872 | 0.7105 | 0.1399 | 0.04736 |
| php_exit_single | 1731 | 8 | 8 | 6 | 6 | 18 | 120 | 12 | 0.4141 | 0.1662 | -0.2479 | 0.1662 | 0.634 | 0.1399 | 0.0263 |
| subset_cardinality | 1729 | 8 | 8 | 3 | 3 | 15 | 120 | 12 | 0.3723 | 0.5639 | 0.1916 | 0.5639 | 1.178 | 0.4718 | 0.09203 |
| subset_cardinality | 1730 | 8 | 8 | 3 | 3 | 15 | 120 | 12 | 0.3415 | 0.521 | 0.1794 | 0.521 | 1.088 | 0.4718 | 0.04914 |
| subset_cardinality | 1731 | 8 | 8 | 3 | 3 | 15 | 120 | 12 | 0.3682 | 0.5601 | 0.1919 | 0.5601 | 1.176 | 0.4718 | 0.08829 |
| tseitin_complete | 1729 | 8 | 8 | 6 | 6 | 9 | 123 | 9 | 0.3417 | 0.6004 | 0.2588 | 0.6004 | 0.8966 | 0.7741 | -0.1737 |
| tseitin_complete | 1730 | 8 | 8 | 6 | 6 | 9 | 123 | 9 | 0.3473 | 0.7371 | 0.3898 | 0.7371 | 1.095 | 0.7741 | -0.03695 |
| tseitin_complete | 1731 | 8 | 8 | 6 | 6 | 9 | 123 | 9 | 0.3134 | 0.6063 | 0.2929 | 0.6063 | 0.9088 | 0.7741 | -0.1678 |
| vertex_cover_torus | 1729 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.1893 | 0.7534 | 0.5641 | 0.7534 | 0.8885 | 1.151 | -0.3977 |
| vertex_cover_torus | 1730 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.2681 | 0.9485 | 0.6804 | 0.9485 | 1.117 | 1.151 | -0.2025 |
| vertex_cover_torus | 1731 | 8 | 8 | 15 | 12 | 15 | 120 | 12 | 0.2314 | 0.8624 | 0.631 | 0.8624 | 1.002 | 1.151 | -0.2886 |

## Evaluation Family Matrix

| heldout_family | eval_family | adapter_train_split | seeds | valid_rollout_rows | mean_adapter_gain_valid_mean | mean_adapter_gain_valid_std | mean_adapted_mu_range_valid_mean | max_adapted_mu_range_valid_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | complete_coloring | heldout | 3 | 3 | 0.9719 | 0.1183 | 0.9719 | 1.117 |
| complete_coloring | dominating_set_hex | train | 3 | 33 | 0.2616 | 0.03187 | 0.2616 | 0.7335 |
| complete_coloring | even_colouring | train | 3 | 42 | 0.08667 | 0.015 | 0.08667 | 0.5476 |
| complete_coloring | php | train | 3 | 3 | 1.043 | 0.1448 | 1.043 | 1.286 |
| complete_coloring | php_exit_all | train | 3 | 6 | 0.37 | 0.03098 | 0.37 | 0.8391 |
| complete_coloring | php_exit_single | train | 3 | 12 | 0.1599 | 0.0196 | 0.1599 | 0.6577 |
| complete_coloring | subset_cardinality | train | 3 | 12 | 0.502 | 0.05571 | 0.502 | 1.16 |
| complete_coloring | tseitin_complete | train | 3 | 9 | 0.9213 | 0.1254 | 0.9213 | 1.503 |
| complete_coloring | vertex_cover_torus | train | 3 | 12 | 1.266 | 0.1098 | 1.266 | 1.576 |
| dominating_set_hex | complete_coloring | train | 3 | 3 | 0.89 | 0.04284 | 0.89 | 0.9612 |
| dominating_set_hex | dominating_set_hex | heldout | 3 | 33 | 0.2436 | 0.02932 | 0.2436 | 0.6964 |
| dominating_set_hex | even_colouring | train | 3 | 42 | 0.07986 | 0.01264 | 0.07986 | 0.5011 |
| dominating_set_hex | php | train | 3 | 3 | 0.9478 | 0.06827 | 0.9478 | 1.096 |
| dominating_set_hex | php_exit_all | train | 3 | 6 | 0.3357 | 0.03175 | 0.3357 | 0.7233 |
| dominating_set_hex | php_exit_single | train | 3 | 12 | 0.1497 | 0.0224 | 0.1497 | 0.6235 |
| dominating_set_hex | subset_cardinality | train | 3 | 12 | 0.4522 | 0.02851 | 0.4522 | 1.03 |
| dominating_set_hex | tseitin_complete | train | 3 | 9 | 0.823 | 0.1024 | 0.823 | 1.332 |
| dominating_set_hex | vertex_cover_torus | train | 3 | 12 | 1.193 | 0.0884 | 1.193 | 1.42 |
| even_colouring | complete_coloring | train | 3 | 3 | 0.7448 | 0.04644 | 0.7448 | 0.835 |
| even_colouring | dominating_set_hex | train | 3 | 33 | 0.1959 | 0.003278 | 0.1959 | 0.5792 |
| even_colouring | even_colouring | heldout | 3 | 42 | 0.04838 | 0.001603 | 0.04838 | 0.2545 |
| even_colouring | php | train | 3 | 3 | 0.7884 | 0.04612 | 0.7884 | 0.9346 |
| even_colouring | php_exit_all | train | 3 | 6 | 0.2637 | 0.003657 | 0.2637 | 0.6701 |
| even_colouring | php_exit_single | train | 3 | 12 | 0.1059 | 0.001573 | 0.1059 | 0.4124 |
| even_colouring | subset_cardinality | train | 3 | 12 | 0.3757 | 0.0237 | 0.3757 | 0.9709 |
| even_colouring | tseitin_complete | train | 3 | 9 | 0.5661 | 0.02656 | 0.5661 | 0.9152 |
| even_colouring | vertex_cover_torus | train | 3 | 12 | 1.003 | 0.02969 | 1.003 | 1.207 |
| php | complete_coloring | train | 3 | 3 | 0.7892 | 0.136 | 0.7892 | 0.9419 |
| php | dominating_set_hex | train | 3 | 33 | 0.2459 | 0.01877 | 0.2459 | 0.7181 |
| php | even_colouring | train | 3 | 42 | 0.07785 | 0.008037 | 0.07785 | 0.4736 |
| php | php | heldout | 3 | 3 | 0.8442 | 0.1357 | 0.8442 | 1.07 |
| php | php_exit_all | train | 3 | 6 | 0.3365 | 0.02741 | 0.3365 | 0.812 |
| php | php_exit_single | train | 3 | 12 | 0.1414 | 0.005849 | 0.1414 | 0.5648 |
| php | subset_cardinality | train | 3 | 12 | 0.4562 | 0.05554 | 0.4562 | 1.151 |
| php | tseitin_complete | train | 3 | 9 | 0.8481 | 0.05844 | 0.8481 | 1.35 |
| php | vertex_cover_torus | train | 3 | 12 | 1.143 | 0.00843 | 1.143 | 1.378 |
| php_exit_all | complete_coloring | train | 3 | 3 | 1.068 | 0.1573 | 1.068 | 1.249 |
| php_exit_all | dominating_set_hex | train | 3 | 33 | 0.2638 | 0.008825 | 0.2638 | 0.7549 |
| php_exit_all | even_colouring | train | 3 | 42 | 0.07614 | 0.004295 | 0.07614 | 0.4412 |
| php_exit_all | php | train | 3 | 3 | 1.082 | 0.1359 | 1.082 | 1.244 |
| php_exit_all | php_exit_all | heldout | 3 | 6 | 0.384 | 0.01839 | 0.384 | 0.9647 |
| php_exit_all | php_exit_single | train | 3 | 12 | 0.1606 | 0.009299 | 0.1606 | 0.6344 |
| php_exit_all | subset_cardinality | train | 3 | 12 | 0.4491 | 0.02863 | 0.4491 | 1.048 |
| php_exit_all | tseitin_complete | train | 3 | 9 | 0.7849 | 0.02478 | 0.7849 | 1.168 |
| php_exit_all | vertex_cover_torus | train | 3 | 12 | 1.319 | 0.04894 | 1.319 | 1.606 |
| php_exit_single | complete_coloring | train | 3 | 3 | 0.9814 | 0.0416 | 0.9814 | 1.077 |
| php_exit_single | dominating_set_hex | train | 3 | 33 | 0.2677 | 0.03044 | 0.2677 | 0.7561 |
| php_exit_single | even_colouring | train | 3 | 42 | 0.08243 | 0.01001 | 0.08243 | 0.4922 |
| php_exit_single | php | train | 3 | 3 | 1.034 | 0.05685 | 1.034 | 1.199 |
| php_exit_single | php_exit_all | train | 3 | 6 | 0.373 | 0.03221 | 0.373 | 0.8174 |
| php_exit_single | php_exit_single | heldout | 3 | 12 | 0.1639 | 0.02457 | 0.1639 | 0.7105 |
| php_exit_single | subset_cardinality | train | 3 | 12 | 0.501 | 0.0229 | 0.501 | 1.133 |
| php_exit_single | tseitin_complete | train | 3 | 9 | 0.8567 | 0.05339 | 0.8567 | 1.295 |
| php_exit_single | vertex_cover_torus | train | 3 | 12 | 1.282 | 0.09559 | 1.282 | 1.518 |
| subset_cardinality | complete_coloring | train | 3 | 3 | 0.9826 | 0.1202 | 0.9826 | 1.163 |
| subset_cardinality | dominating_set_hex | train | 3 | 33 | 0.243 | 0.0129 | 0.243 | 0.6933 |
| subset_cardinality | even_colouring | train | 3 | 42 | 0.07614 | 0.00292 | 0.07614 | 0.4468 |
| subset_cardinality | php | train | 3 | 3 | 1.046 | 0.1283 | 1.046 | 1.303 |
| subset_cardinality | php_exit_all | train | 3 | 6 | 0.3362 | 0.02982 | 0.3362 | 0.8663 |
| subset_cardinality | php_exit_single | train | 3 | 12 | 0.1427 | 0.007759 | 0.1427 | 0.5747 |
| subset_cardinality | subset_cardinality | heldout | 3 | 12 | 0.5483 | 0.02376 | 0.5483 | 1.178 |
| subset_cardinality | tseitin_complete | train | 3 | 9 | 0.8723 | 0.01639 | 0.8723 | 1.329 |
| subset_cardinality | vertex_cover_torus | train | 3 | 12 | 1.2 | 0.05324 | 1.2 | 1.441 |
| tseitin_complete | complete_coloring | train | 3 | 3 | 0.8793 | 0.02031 | 0.8793 | 0.9205 |
| tseitin_complete | dominating_set_hex | train | 3 | 33 | 0.2427 | 0.01393 | 0.2427 | 0.7285 |
| tseitin_complete | even_colouring | train | 3 | 42 | 0.07581 | 0.007206 | 0.07581 | 0.4535 |
| tseitin_complete | php | train | 3 | 3 | 0.9209 | 0.04235 | 0.9209 | 1.044 |
| tseitin_complete | php_exit_all | train | 3 | 6 | 0.3401 | 0.02263 | 0.3401 | 0.8472 |
| tseitin_complete | php_exit_single | train | 3 | 12 | 0.1392 | 0.01064 | 0.1392 | 0.558 |
| tseitin_complete | subset_cardinality | train | 3 | 12 | 0.4795 | 0.03129 | 0.4795 | 1.177 |
| tseitin_complete | tseitin_complete | heldout | 3 | 9 | 0.648 | 0.07729 | 0.648 | 1.095 |
| tseitin_complete | vertex_cover_torus | train | 3 | 12 | 1.253 | 0.05691 | 1.253 | 1.514 |
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

- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_complete_coloring_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_complete_coloring_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_complete_coloring_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_dominating_set_hex_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_dominating_set_hex_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_dominating_set_hex_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_even_colouring_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_even_colouring_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_even_colouring_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_all_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_all_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_all_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_single_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_single_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_php_exit_single_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_subset_cardinality_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_subset_cardinality_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_subset_cardinality_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_tseitin_complete_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_tseitin_complete_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_tseitin_complete_seed1731_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1729_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1730_orbits.csv`
- `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_seed1731_orbits.csv`
