# Static Symmetry Audit

- checkpoint: `runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit measures whether the static GNN guidance assigns nearly
identical `rho` and `mu` outputs to variables in the same hand-labelled
symmetry orbit, and how stable orbit means are under variable renaming.

## Orbit Collapse

| family | instances | orbits | valid_orbit_rows | mean_rho_range | max_rho_range | mean_mu_range | max_mu_range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 15 | 15 | 15 | 5.325e-07 | 8.345e-07 | 2.26e-08 | 4.843e-08 |

## Orbit Row Filter

| family | orbit_valid_reason | rows |
| --- | --- | --- |
| vertex_cover_torus | valid | 15 |

## Permutation Stability

| family | groups | mean_rho_variant_std | max_rho_variant_std | mean_mu_variant_std | max_mu_variant_std |
| --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 5 | 1.896e-07 | 4.139e-07 | 2.191e-08 | 1.013e-07 |
