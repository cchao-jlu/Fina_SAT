# EchoSAT Symmetry GRPO v1.4 Strict-Best Validation Set

This validation set is only for online best-checkpoint selection. It is not a new runtime benchmark and does not support a solver speedup claim.

## Artifacts

- manifest: `runs/analysis/echosat_symmetry_grpo_v1_4_strictbest_val_manifest.csv`
- file list: `runs/analysis/echosat_symmetry_grpo_v1_4_strictbest_val_files.txt`

## Summary

| strictbest_validation_role | family | rows | bases | variants | split_source |
| --- | --- | --- | --- | --- | --- |
| anchor | complete_coloring | 3 | 1 | 3 | echosat_runtime_v12_canonical |
| anchor | php | 17 | 1 | 17 | echosat_runtime_v12_canonical,symmetry_grpo_speedup_full |
| control | random_3sat_control | 68 | 4 | 17 | symmetry_grpo_speedup_full |
| hard_negative | complete_coloring | 3 | 1 | 3 | echosat_runtime_v12_canonical |
| hard_negative | php | 17 | 1 | 17 | echosat_runtime_v12_canonical,symmetry_grpo_speedup_full |
| subset_failure_guard | subset_cardinality | 17 | 1 | 17 | echosat_runtime_v12_canonical,symmetry_grpo_speedup_full |

## Base Instances

| strictbest_validation_role | family | base_instance_id | rows | variants |
| --- | --- | --- | --- | --- |
| anchor | complete_coloring | k9_color8 | 3 | 3 |
| anchor | php | php_p9_h8 | 17 | 17 |
| control | random_3sat_control | random_3sat_control_v20_c85_seed1901 | 17 | 17 |
| control | random_3sat_control | random_3sat_control_v24_c102_seed1921 | 17 | 17 |
| control | random_3sat_control | random_3sat_control_v55_c234_seed1926 | 17 | 17 |
| control | random_3sat_control | random_3sat_control_v70_c298_seed1928 | 17 | 17 |
| hard_negative | complete_coloring | k10_color9 | 3 | 3 |
| hard_negative | php | php_p10_h9 | 17 | 17 |
| subset_failure_guard | subset_cardinality | subset_cardinality_bw12 | 17 | 17 |

## Intended Use

- Training still uses the full canonical train split.
- Validation uses this file list so `echosat_strict_search_work_v2` can see anchors, hard negatives, subset failure guard, and random-control suppression rows.
- `best.pt` may be absent if no validation checkpoint passes hard gates; use `iter=*.pt` plus targeted acceptance in that case.
