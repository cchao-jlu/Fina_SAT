# Static Symmetry Audit

- checkpoint: `runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit measures whether the static GNN guidance assigns nearly
identical `rho` and `mu` outputs to variables in the same hand-labelled
symmetry orbit, and how stable orbit means are under variable renaming.

## Orbit Collapse

| family | instances | orbits | mean_rho_range | max_rho_range | mean_mu_range | max_mu_range |
| --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 6 | 6 | 3.725e-07 | 5.662e-07 | 1.987e-08 | 2.98e-08 |
| dominating_set_hex | 3 | 3 | 0.01311 | 0.01311 | 0.0002246 | 0.0002246 |
| even_colouring | 3 | 6 | 0.3482 | 0.6965 | 0.04902 | 0.09803 |
| php | 6 | 6 | 3.725e-07 | 5.662e-07 | 1.987e-08 | 2.98e-08 |
| php_exit_all | 3 | 6 | 5.215e-07 | 7.749e-07 | 2.732e-08 | 3.725e-08 |
| php_exit_single | 3 | 6 | 0.2777 | 0.5554 | 0.002001 | 0.004003 |
| subset_cardinality | 3 | 6 | 0.09917 | 0.1252 | 0.003769 | 0.006008 |
| tseitin_complete | 6 | 9 | 2.053e-07 | 2.682e-07 | 3.601e-08 | 5.588e-08 |
| vertex_cover_torus | 3 | 3 | 7.351e-07 | 8.345e-07 | 3.353e-08 | 4.843e-08 |

## Permutation Stability

| family | groups | mean_rho_variant_std | max_rho_variant_std | mean_mu_variant_std | max_mu_variant_std |
| --- | --- | --- | --- | --- | --- |
| complete_coloring | 2 | 5.089e-08 | 8.774e-08 | 0 | 0 |
| dominating_set_hex | 1 | 0 | 0 | 5.268e-09 | 5.268e-09 |
| even_colouring | 2 | 1.581e-08 | 1.756e-08 | 1.756e-09 | 3.512e-09 |
| php | 2 | 5.089e-08 | 8.774e-08 | 0 | 0 |
| php_exit_all | 2 | 3.838e-08 | 4.867e-08 | 1.756e-09 | 3.512e-09 |
| php_exit_single | 2 | 2.639e-07 | 4.496e-07 | 1.581e-08 | 2.81e-08 |
| subset_cardinality | 2 | 8.285e-08 | 1.127e-07 | 1.756e-09 | 3.512e-09 |
| tseitin_complete | 3 | 1.873e-08 | 4.215e-08 | 2.927e-09 | 3.512e-09 |
| vertex_cover_torus | 1 | 4.139e-07 | 4.139e-07 | 1.013e-07 | 1.013e-07 |
