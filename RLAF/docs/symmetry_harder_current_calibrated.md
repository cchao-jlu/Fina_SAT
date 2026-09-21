# SAT Symmetry Harder Baseline

This dataset is a harder baseline candidate pool for comparing SAT symmetry checkpoints against plain Glucose. It is separate from v1/v2 and GRPO training artifacts.

The target subset is selected by base-instance plain Glucose calibration. Permutation variants are included only after a base enters the target band.

## Outputs

- full manifest: `runs/analysis/symmetry_harder_baseline_manifest.csv`
- base calibration: `runs/analysis/symmetry_harder_baseline_plain_glucose_calibration.csv`
- target manifest: `runs/analysis/symmetry_harder_baseline_target_manifest.csv`

## Headline

- full base instances: 76
- full manifest rows: 228
- target base instances: 5
- target manifest rows: 15

The target band is not a speedup claim. It only identifies instances where plain Glucose is not trivially fast and is still solved under the calibration cap.

## Full Candidate Summary

| family | control_type | base_instances | rows | max_clauses |
| --- | --- | --- | --- | --- |
| complete_coloring | strong_symmetry | 12 | 36 | 1221 |
| dominating_set_hex | weak_symmetry | 4 | 12 | 54285 |
| even_colouring | weak_symmetry | 3 | 9 | 242 |
| php | strong_symmetry | 7 | 21 | 1807 |
| php_exit_all | weak_symmetry | 5 | 15 | 1111 |
| php_exit_single | weak_symmetry | 7 | 21 | 1807 |
| random_3sat_control | non_symmetric_control | 21 | 63 | 1266 |
| subset_cardinality | weak_symmetry | 5 | 15 | 172 |
| tseitin_complete | strong_symmetry | 8 | 24 | 2560 |
| vertex_cover_torus | strong_symmetry | 4 | 12 | 168000 |

## Calibration Bands

| difficulty_band | family | base_instances | mean_cpu | median_cpu |
| --- | --- | --- | --- | --- |
| target_harder_baseline | complete_coloring | 1 | 3.11061 | 3.11061 |
| target_harder_baseline | php | 1 | 3.72077 | 3.72077 |
| target_harder_baseline | random_3sat_control | 1 | 2.0067 | 2.0067 |
| target_harder_baseline | tseitin_complete | 1 | 4.77427 | 4.77427 |
| target_harder_baseline | vertex_cover_torus | 1 | 9.16013 | 9.16013 |
| timeout_or_indeterminate | complete_coloring | 1 | 9.94097 | 9.94097 |
| timeout_or_indeterminate | php | 3 | 9.947 | 9.95012 |
| timeout_or_indeterminate | tseitin_complete | 2 | 10.064 | 10.064 |
| too_easy | complete_coloring | 10 | 0.0522848 | 0.0010665 |
| too_easy | dominating_set_hex | 4 | 0.643523 | 0.577584 |
| too_easy | even_colouring | 3 | 0.000727333 | 0.000707 |
| too_easy | php | 3 | 0.171342 | 0.020811 |
| too_easy | php_exit_all | 5 | 0.0009224 | 0.000886 |
| too_easy | php_exit_single | 7 | 0.000878 | 0.000882 |
| too_easy | random_3sat_control | 20 | 0.0742398 | 0.0029935 |
| too_easy | subset_cardinality | 5 | 0.0018794 | 0.001686 |
| too_easy | tseitin_complete | 5 | 0.0076832 | 0.002306 |
| too_easy | vertex_cover_torus | 3 | 0.808208 | 0.622277 |

## Target Bases

| family | base_instance_id | expected_result | num_vars | num_clauses | plain_glucose_result | plain_glucose_cpu_time | plain_glucose_decisions | plain_glucose_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | UNKNOWN | 260 | 1113 | UNSATISFIABLE | 2.0067 | 167986 | 145890 |
| complete_coloring | k10_color9 | UNSATISFIABLE | 90 | 775 | UNSATISFIABLE | 3.11061 | 604963 | 534806 |
| php | php_p10_h9 | UNSATISFIABLE | 90 | 775 | UNSATISFIABLE | 3.72077 | 734102 | 641326 |
| tseitin_complete | tseitin_k8_odd | UNSATISFIABLE | 28 | 512 | UNSATISFIABLE | 4.77427 | 899041 | 595619 |
| vertex_cover_torus | vertex_cover_torus_4x5_k8_event | UNSATISFIABLE | 20 | 168000 | UNSATISFIABLE | 9.16013 | 24 | 24 |
