# EchoSAT Formula Equivalence Audit v1

This audit checks whether harder-baseline family labels correspond to distinct CNFs. It is offline only: no solver jobs, no training, and no gate/selector is fitted.

## Artifacts

- hash rows CSV: `runs/analysis/echosat_formula_equivalence_v1_hash_rows.csv`
- equivalence classes CSV: `runs/analysis/echosat_formula_equivalence_v1_classes.csv`
- runtime pair deltas CSV: `runs/analysis/echosat_formula_equivalence_v1_runtime_pairs.csv`

## Cross-Family Formula Classes

| parsed_num_vars | parsed_num_clauses | rows | families | base_instances | variants | file_hash_count | ordered_hash_count | clause_length_hist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 72 | 549 | 2 | complete_coloring,php | k9_color8,php_p9_h8 | perm_seed1730 | 2 | 2 | 2:540;8:9 |
| 72 | 549 | 2 | complete_coloring,php | k9_color8,php_p9_h8 | perm_seed1731 | 2 | 2 | 2:540;8:9 |
| 72 | 549 | 2 | complete_coloring,php | k9_color8,php_p9_h8 | base | 2 | 2 | 2:540;8:9 |
| 90 | 775 | 2 | complete_coloring,php | k10_color9,php_p10_h9 | perm_seed1731 | 2 | 2 | 2:765;9:10 |
| 90 | 775 | 2 | complete_coloring,php | k10_color9,php_p10_h9 | base | 2 | 2 | 2:765;9:10 |
| 90 | 775 | 2 | complete_coloring,php | k10_color9,php_p10_h9 | perm_seed1730 | 2 | 2 | 2:765;9:10 |

## Complete Coloring vs PHP Runtime Pair Summary

| warmup_conflicts | parsed_num_vars | parsed_num_clauses | pairs | same_unordered_formula | same_ordered_dimacs_fraction | complete_minus_php_adapter_cached_delta_mean | complete_minus_php_adapter_plain_protocol_delta_mean | complete_minus_php_plain_cpu_mean | complete_minus_php_event_l2_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 72 | 549 | 9 | True | 0 | -0.0112183 | 0.0500728 | -0.0547744 | 0.0533727 |
| 1 | 90 | 775 | 9 | True | 0 | -0.26206 | -0.504905 | 0.279062 | -0.082255 |
| 3 | 72 | 549 | 9 | True | 0 | -0.0444448 | 0.0438083 | -0.0616386 | -0.0807749 |
| 3 | 90 | 775 | 9 | True | 0 | -0.417357 | -0.641983 | 0.295134 | 0.303111 |
| 5 | 72 | 549 | 9 | True | 0 | -0.0349482 | 0.0632786 | -0.0588816 | -0.15242 |
| 5 | 90 | 775 | 9 | True | 0 | -0.434204 | -0.628855 | 0.293238 | 0.854172 |
| 10 | 72 | 549 | 9 | True | 0 | -0.0301641 | 0.0514906 | -0.0599668 | -1.46426 |
| 10 | 90 | 775 | 9 | True | 0 | -0.0411322 | -0.258784 | 0.289133 | -3.43484 |
| 20 | 72 | 549 | 9 | True | 0 | -0.0254482 | 0.0654949 | -0.0593614 | 0.257772 |
| 20 | 90 | 775 | 9 | True | 0 | -0.675514 | -0.873963 | 0.288861 | -1.08136 |

## Interpretation

- `same_unordered_formula=True` means the two family labels encode the same clause set after ignoring clause order.
- Different `ordered_dimacs_sha256` or `file_sha256` still matters for CDCL runs because clause order can affect the solver path.
- If complete_coloring and php differ on runtime while sharing the same unordered formula, this cannot be claimed as a family-specific symmetry mechanism from CNF structure alone.
- The next protocol step should treat these rows as formula-equivalent ordering/permutation diagnostics unless a future run canonicalizes DIMACS order or explicitly models order sensitivity.
