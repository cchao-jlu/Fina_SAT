# SAT Symmetry Harder Baseline

This dataset is a harder baseline candidate pool for comparing SAT symmetry checkpoints against plain Glucose. It is separate from v1/v2 and GRPO training artifacts.

The target subset is selected by base-instance plain Glucose calibration. Permutation variants are included only after a base enters the target band.

## Outputs

- full manifest: `runs/analysis/symmetry_harder_baseline_manifest.csv`
- base calibration: `runs/analysis/symmetry_harder_baseline_plain_glucose_calibration.csv`
- target manifest: `runs/analysis/symmetry_harder_baseline_target_manifest.csv`

## Headline

- full base instances: 76
- full manifest rows: 532
- target base instances: 14
- target manifest rows: 98

The target band is not a speedup claim. It only identifies instances where plain Glucose is not trivially fast and is still solved under the calibration cap.

## Full Candidate Summary

| family | control_type | base_instances | rows | max_clauses |
| --- | --- | --- | --- | --- |
| complete_coloring | strong_symmetry | 12 | 84 | 1221 |
| dominating_set_hex | weak_symmetry | 4 | 28 | 54285 |
| even_colouring | weak_symmetry | 3 | 21 | 242 |
| php | strong_symmetry | 7 | 49 | 1807 |
| php_exit_all | weak_symmetry | 5 | 35 | 1111 |
| php_exit_single | weak_symmetry | 7 | 49 | 1807 |
| random_3sat_control | non_symmetric_control | 21 | 147 | 1266 |
| subset_cardinality | weak_symmetry | 5 | 35 | 172 |
| tseitin_complete | strong_symmetry | 8 | 56 | 2560 |
| vertex_cover_torus | strong_symmetry | 4 | 28 | 168000 |

## Calibration Bands

| difficulty_band | family | base_instances | mean_cpu | median_cpu |
| --- | --- | --- | --- | --- |
| above_or_unsolved_xhard | complete_coloring | 1 | 9.99956 | 9.99956 |
| above_or_unsolved_xhard | php | 3 | 10.0209 | 10.0035 |
| above_or_unsolved_xhard | tseitin_complete | 3 | 11.0079 | 10.1676 |
| above_or_unsolved_xhard | vertex_cover_torus | 1 | 10.0007 | 10.0007 |
| below_xhard_min | complete_coloring | 9 | 0.00806867 | 0.002313 |
| below_xhard_min | dominating_set_hex | 1 | 0.128188 | 0.128188 |
| below_xhard_min | even_colouring | 3 | 0.00176667 | 0.002537 |
| below_xhard_min | php | 2 | 0.0275145 | 0.0275145 |
| below_xhard_min | php_exit_all | 5 | 0.002637 | 0.002951 |
| below_xhard_min | php_exit_single | 7 | 0.00201686 | 0.001571 |
| below_xhard_min | random_3sat_control | 17 | 0.0301513 | 0.007383 |
| below_xhard_min | subset_cardinality | 5 | 0.006088 | 0.005883 |
| below_xhard_min | tseitin_complete | 5 | 0.0227368 | 0.01366 |
| target_xhard_perm6 | complete_coloring | 2 | 3.96296 | 3.96296 |
| target_xhard_perm6 | dominating_set_hex | 3 | 3.23637 | 2.32357 |
| target_xhard_perm6 | php | 2 | 4.56131 | 4.56131 |
| target_xhard_perm6 | random_3sat_control | 4 | 1.91657 | 1.18101 |
| target_xhard_perm6 | vertex_cover_torus | 3 | 3.72369 | 2.84404 |

## Target Bases

_empty_
