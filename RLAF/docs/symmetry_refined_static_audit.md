# Static Symmetry Audit

- checkpoint: `runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit measures whether the static GNN guidance assigns nearly
identical `rho` and `mu` outputs to variables in the same hand-labelled
symmetry orbit, and how stable orbit means are under variable renaming.

## Orbit Collapse

| family | instances | orbits | valid_orbit_rows | mean_rho_range | max_rho_range | mean_mu_range | max_mu_range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 6 | 6 | 3.725e-07 | 5.662e-07 | 1.987e-08 | 2.98e-08 |
| dominating_set_hex | 12 | 105 | 105 | 2.558e-06 | 2.807e-05 | 5.407e-08 | 2.57e-07 |
| even_colouring | 3 | 42 | 42 | 1.958e-07 | 5.066e-07 | 2.936e-08 | 1.416e-07 |
| php | 6 | 6 | 6 | 3.725e-07 | 5.662e-07 | 1.987e-08 | 2.98e-08 |
| php_exit_all | 3 | 6 | 6 | 5.215e-07 | 7.749e-07 | 2.732e-08 | 3.725e-08 |
| php_exit_single | 6 | 12 | 12 | 2.471e-07 | 5.96e-07 | 2.359e-08 | 4.47e-08 |
| subset_cardinality | 3 | 12 | 12 | 2.049e-07 | 3.725e-07 | 1.925e-08 | 2.98e-08 |
| tseitin_complete | 6 | 9 | 9 | 2.053e-07 | 2.682e-07 | 3.601e-08 | 5.588e-08 |
| vertex_cover_torus | 15 | 15 | 15 | 5.325e-07 | 8.345e-07 | 2.26e-08 | 4.843e-08 |

## Orbit Row Filter

| family | orbit_valid_reason | rows |
| --- | --- | --- |
| complete_coloring | valid | 6 |
| dominating_set_hex | orbit_size_below_min | 33 |
| dominating_set_hex | valid | 105 |
| even_colouring | orbit_size_below_min | 3 |
| even_colouring | valid | 42 |
| php | valid | 6 |
| php_exit_all | valid | 6 |
| php_exit_single | orbit_size_below_min | 6 |
| php_exit_single | valid | 12 |
| subset_cardinality | orbit_size_below_min | 3 |
| subset_cardinality | valid | 12 |
| tseitin_complete | valid | 9 |
| vertex_cover_torus | valid | 15 |

## Permutation Stability

| family | groups | mean_rho_variant_std | max_rho_variant_std | mean_mu_variant_std | max_mu_variant_std |
| --- | --- | --- | --- | --- | --- |
| complete_coloring | 2 | 5.089e-08 | 8.774e-08 | 0 | 0 |
| dominating_set_hex | 35 | 5.65e-08 | 1.487e-07 | 3.578e-09 | 8.048e-09 |
| even_colouring | 14 | 5.353e-08 | 1.221e-07 | 7.487e-09 | 1.979e-08 |
| php | 2 | 5.089e-08 | 8.774e-08 | 0 | 0 |
| php_exit_all | 2 | 3.838e-08 | 4.867e-08 | 1.756e-09 | 3.512e-09 |
| php_exit_single | 4 | 4.629e-08 | 8.429e-08 | 5.268e-09 | 7.024e-09 |
| subset_cardinality | 4 | 7.645e-08 | 1.312e-07 | 5.676e-09 | 1.217e-08 |
| tseitin_complete | 3 | 1.873e-08 | 4.215e-08 | 2.927e-09 | 3.512e-09 |
| vertex_cover_torus | 5 | 1.896e-07 | 4.139e-07 | 2.191e-08 | 1.013e-07 |
