# Weighted Glucose Path Audit

This audit diagnoses the guided-loss rows from the symmetry solver protocol preflight.
It is not a solver speedup claim. It separates the weighted binary path from the `c weight` input path and from the all-positive neutral phase convention.

## Setup

- manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_stress_manifest.csv`
- repeats: `3`
- seed base: `1`
- cpu limit: `5.0`
- selected base instances: `dominating_set_hex_4x5_s5, vertex_cover_torus_4x5_norat`

## Probes

- `plain_glucose_no_weight`: Plain Glucose binary with the original DIMACS input.
- `plain_glucose_pos_weight_comment`: Plain Glucose binary with a c weight all +1.0 comment line, which plain Glucose ignores.
- `weighted_glucose_no_weight`: Weighted Glucose binary with the original DIMACS input and no c weight line.
- `weighted_glucose_all_pos_weight`: Weighted Glucose binary with the current neutral baseline input: all +1.0 weights.
- `weighted_glucose_all_neg_weight`: Weighted Glucose binary with all -1.0 weights, matching the default Glucose polarity sign in the weighted parser.

Note: in `solvers/glucose_weighted/core/Dimacs.h`, a positive `c weight` entry calls `newVar(false, ...)`, while a negative entry calls `newVar(true, ...)`. The unweighted Glucose parser creates variables with the default `newVar(true)` polarity. Therefore all `+1.0` is a uniform phase baseline, but it is not the default Glucose polarity baseline.

## Base Attribution

| family | base_instance_id | primary_weighted_path_attribution | plain_all_solved | plain_pos_comment_all_solved | weighted_no_weight_all_solved | weighted_all_pos_all_solved | weighted_all_neg_all_solved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_4x5_s5 | weighted_path_loss_not_reproduced | True | True | True | True | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | weighted_path_loss_not_reproduced | True | True | True | True | True |

## Method Summary

| family | base_instance_id | method | rows | solved_rows | indeterminate_rows | mean_cpu_time | mean_decisions | mean_conflicts | weight_echo_lines_mean | result_consistent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dominating_set_hex | dominating_set_hex_4x5_s5 | plain_glucose_no_weight | 9 | 9 | 0 | 2.28 | 10 | 0.3333 | 0 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | plain_glucose_pos_weight_comment | 9 | 9 | 0 | 2.287 | 10 | 0.3333 | 0 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | weighted_glucose_no_weight | 9 | 9 | 0 | 4.997 | 14.67 | 0 | 0 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | weighted_glucose_all_pos_weight | 9 | 9 | 0 | 5 | 101 | 68.67 | 20 | True |
| dominating_set_hex | dominating_set_hex_4x5_s5 | weighted_glucose_all_neg_weight | 9 | 9 | 0 | 5 | 14.67 | 0 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | plain_glucose_no_weight | 9 | 9 | 0 | 4.999 | 16.33 | 16.33 | 0 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | plain_glucose_pos_weight_comment | 9 | 9 | 0 | 4.998 | 16.33 | 16.33 | 0 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | weighted_glucose_no_weight | 9 | 9 | 0 | 5.001 | 16.33 | 16.33 | 0 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | weighted_glucose_all_pos_weight | 9 | 9 | 0 | 5.005 | 16 | 16 | 20 | True |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | weighted_glucose_all_neg_weight | 9 | 9 | 0 | 4.998 | 16.33 | 16.33 | 20 | True |

## Per-Variant Rows

| repeat_id | family | base_instance_id | variant | method | result | cpu_time | decisions | conflicts | weight_echo_lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_no_weight | SATISFIABLE | 2.291 | 8 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_pos_weight_comment | SATISFIABLE | 2.284 | 8 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_no_weight | SATISFIABLE | 4.996 | 15 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_pos_weight | SATISFIABLE | 5.001 | 63 | 43 | 20 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_neg_weight | SATISFIABLE | 5.002 | 15 | 0 | 20 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_no_weight | SATISFIABLE | 2.299 | 12 | 1 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.284 | 12 | 1 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_no_weight | SATISFIABLE | 4.996 | 14 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_pos_weight | SATISFIABLE | 5.008 | 181 | 132 | 20 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_neg_weight | SATISFIABLE | 4.999 | 14 | 0 | 20 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_no_weight | SATISFIABLE | 2.28 | 10 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.342 | 10 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_no_weight | SATISFIABLE | 5.001 | 15 | 0 | 0 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_pos_weight | SATISFIABLE | 4.998 | 59 | 31 | 20 |
| 0 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_neg_weight | SATISFIABLE | 5.002 | 15 | 0 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_no_weight | UNSATISFIABLE | 5 | 15 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_pos_weight_comment | UNSATISFIABLE | 4.996 | 15 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_no_weight | UNSATISFIABLE | 4.99 | 15 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_pos_weight | UNSATISFIABLE | 5.013 | 18 | 18 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_neg_weight | UNSATISFIABLE | 5.001 | 15 | 16 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | plain_glucose_no_weight | UNSATISFIABLE | 4.995 | 18 | 17 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | plain_glucose_pos_weight_comment | UNSATISFIABLE | 4.999 | 18 | 17 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_no_weight | UNSATISFIABLE | 5.011 | 18 | 17 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_all_pos_weight | UNSATISFIABLE | 5.009 | 15 | 16 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_all_neg_weight | UNSATISFIABLE | 4.998 | 18 | 17 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | plain_glucose_no_weight | UNSATISFIABLE | 4.999 | 16 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | plain_glucose_pos_weight_comment | UNSATISFIABLE | 4.989 | 16 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_no_weight | UNSATISFIABLE | 4.994 | 16 | 16 | 0 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_all_pos_weight | UNSATISFIABLE | 4.995 | 15 | 14 | 20 |
| 0 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_all_neg_weight | UNSATISFIABLE | 4.999 | 16 | 16 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_no_weight | SATISFIABLE | 2.261 | 8 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_pos_weight_comment | SATISFIABLE | 2.251 | 8 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_no_weight | SATISFIABLE | 5.003 | 15 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_pos_weight | SATISFIABLE | 4.999 | 63 | 43 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_neg_weight | SATISFIABLE | 5.001 | 15 | 0 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_no_weight | SATISFIABLE | 2.279 | 12 | 1 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.291 | 12 | 1 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_no_weight | SATISFIABLE | 5.003 | 14 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_pos_weight | SATISFIABLE | 5.002 | 181 | 132 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_neg_weight | SATISFIABLE | 4.996 | 14 | 0 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_no_weight | SATISFIABLE | 2.251 | 10 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.251 | 10 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_no_weight | SATISFIABLE | 4.991 | 15 | 0 | 0 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_pos_weight | SATISFIABLE | 5.002 | 59 | 31 | 20 |
| 1 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_neg_weight | SATISFIABLE | 5.002 | 15 | 0 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_no_weight | UNSATISFIABLE | 4.993 | 15 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_pos_weight_comment | UNSATISFIABLE | 5.005 | 15 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_no_weight | UNSATISFIABLE | 5.003 | 15 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_pos_weight | UNSATISFIABLE | 5.008 | 18 | 18 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_neg_weight | UNSATISFIABLE | 4.995 | 15 | 16 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | plain_glucose_no_weight | UNSATISFIABLE | 4.996 | 18 | 17 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | plain_glucose_pos_weight_comment | UNSATISFIABLE | 4.991 | 18 | 17 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_no_weight | UNSATISFIABLE | 5.011 | 18 | 17 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_all_pos_weight | UNSATISFIABLE | 4.998 | 15 | 16 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1730 | weighted_glucose_all_neg_weight | UNSATISFIABLE | 4.998 | 18 | 17 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | plain_glucose_no_weight | UNSATISFIABLE | 5.011 | 16 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | plain_glucose_pos_weight_comment | UNSATISFIABLE | 5.002 | 16 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_no_weight | UNSATISFIABLE | 5.003 | 16 | 16 | 0 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_all_pos_weight | UNSATISFIABLE | 5 | 15 | 14 | 20 |
| 1 | vertex_cover_torus | vertex_cover_torus_4x5_norat | perm_seed1731 | weighted_glucose_all_neg_weight | UNSATISFIABLE | 5.006 | 16 | 16 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_no_weight | SATISFIABLE | 2.267 | 8 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | plain_glucose_pos_weight_comment | SATISFIABLE | 2.266 | 8 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_no_weight | SATISFIABLE | 4.998 | 15 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_pos_weight | SATISFIABLE | 5 | 63 | 43 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | base | weighted_glucose_all_neg_weight | SATISFIABLE | 5.002 | 15 | 0 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_no_weight | SATISFIABLE | 2.315 | 12 | 1 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.323 | 12 | 1 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_no_weight | SATISFIABLE | 4.994 | 14 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_pos_weight | SATISFIABLE | 5.001 | 181 | 132 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1730 | weighted_glucose_all_neg_weight | SATISFIABLE | 4.995 | 14 | 0 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_no_weight | SATISFIABLE | 2.28 | 10 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | plain_glucose_pos_weight_comment | SATISFIABLE | 2.296 | 10 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_no_weight | SATISFIABLE | 4.993 | 15 | 0 | 0 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_pos_weight | SATISFIABLE | 4.993 | 59 | 31 | 20 |
| 2 | dominating_set_hex | dominating_set_hex_4x5_s5 | perm_seed1731 | weighted_glucose_all_neg_weight | SATISFIABLE | 5.001 | 15 | 0 | 20 |
| 2 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_no_weight | UNSATISFIABLE | 5 | 15 | 16 | 0 |
| 2 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | plain_glucose_pos_weight_comment | UNSATISFIABLE | 5.002 | 15 | 16 | 0 |
| 2 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_no_weight | UNSATISFIABLE | 4.999 | 15 | 16 | 0 |
| 2 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_pos_weight | UNSATISFIABLE | 5.006 | 18 | 18 | 20 |
| 2 | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | weighted_glucose_all_neg_weight | UNSATISFIABLE | 4.99 | 15 | 16 | 20 |

## Interpretation

- If `plain_glucose_pos_weight_comment` matches `plain_glucose_no_weight`, the literal comment line itself is harmless for plain Glucose.
- If `weighted_glucose_no_weight` matches plain Glucose, the weighted binary without parsed weights is not the observed loss source.
- If `weighted_glucose_all_neg_weight` solves but `weighted_glucose_all_pos_weight` loses, the current all-positive neutral baseline is exposing a phase/polarity convention problem rather than adapter delta.
- If all weighted probes solve on the selected loss cases, the previous weighted-path loss is not reproduced by the current binary.
- If all weighted probes lose, the next target is the weighted binary core/preprocessing path.

