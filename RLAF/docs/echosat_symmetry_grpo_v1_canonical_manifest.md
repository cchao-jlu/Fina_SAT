# EchoSAT Symmetry GRPO v1 Canonical Manifest

This training manifest rewrites the existing large symmetry GRPO split into canonical DIMACS order and appends the v1.2 canonical hard/order-paired rows. It does not train a model.

## Artifacts

- manifest CSV: `runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv`
- canonical data root: `data/echosat_symmetry_grpo_v1_canonical`

## Summary

| split | family | rows | bases | sampling_groups | priority_rows | control_rows |
| --- | --- | --- | --- | --- | --- | --- |
| train | complete_coloring | 125 | 9 | 9 | 6 | 0 |
| train | dominating_set_hex | 17 | 1 | 1 | 0 | 0 |
| train | even_colouring | 68 | 4 | 4 | 0 | 0 |
| train | php | 105 | 7 | 7 | 34 | 0 |
| train | php_exit_all | 71 | 5 | 5 | 0 | 0 |
| train | php_exit_single | 102 | 6 | 6 | 0 | 0 |
| train | random_3sat_control | 344 | 26 | 26 | 344 | 344 |
| train | subset_cardinality | 88 | 6 | 6 | 17 | 0 |
| train | tseitin_complete | 136 | 8 | 8 | 0 | 0 |
| train | vertex_cover_torus | 68 | 4 | 4 | 0 | 0 |
| val | complete_coloring | 34 | 2 | 2 | 0 | 0 |
| val | dominating_set_hex | 17 | 1 | 1 | 0 | 0 |
| val | even_colouring | 17 | 1 | 1 | 0 | 0 |
| val | php | 20 | 2 | 2 | 0 | 0 |
| val | php_exit_all | 17 | 1 | 1 | 0 | 0 |
| val | php_exit_single | 20 | 2 | 2 | 0 | 0 |
| val | random_3sat_control | 85 | 5 | 5 | 85 | 85 |
| val | subset_cardinality | 14 | 1 | 1 | 0 | 0 |
| val | tseitin_complete | 34 | 2 | 2 | 0 | 0 |
| val | vertex_cover_torus | 17 | 1 | 1 | 0 | 0 |
| all | all | 1399 | 93 | 91 | 486 | 429 |

## Protocol Notes

- `echosat_sampling_group_id` groups formula-equivalent canonical pairs where known.
- `training_priority > 0` marks repair/control rows for the GRPO sampler.
- Random controls are retained as robustness/control-penalty rows, not positive reward sources.
- Variable ids, orbits, and expected labels are preserved; only DIMACS literal/clause order is normalized.
