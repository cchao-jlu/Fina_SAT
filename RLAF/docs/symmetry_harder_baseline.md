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
- target base instances: 20
- target manifest rows: 60

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
| target_harder_baseline | complete_coloring | 3 | 2.65927 | 1.03784 |
| target_harder_baseline | dominating_set_hex | 4 | 2.45932 | 2.26565 |
| target_harder_baseline | php | 2 | 4.56131 | 4.56131 |
| target_harder_baseline | random_3sat_control | 7 | 1.14444 | 0.661994 |
| target_harder_baseline | tseitin_complete | 1 | 0.074278 | 0.074278 |
| target_harder_baseline | vertex_cover_torus | 3 | 3.72369 | 2.84404 |
| timeout_or_indeterminate | complete_coloring | 1 | 9.99956 | 9.99956 |
| timeout_or_indeterminate | php | 3 | 10.0209 | 10.0035 |
| timeout_or_indeterminate | tseitin_complete | 3 | 11.0079 | 10.1676 |
| too_easy | complete_coloring | 8 | 0.00259088 | 0.0020085 |
| too_easy | even_colouring | 3 | 0.00176667 | 0.002537 |
| too_easy | php | 2 | 0.0275145 | 0.0275145 |
| too_easy | php_exit_all | 5 | 0.002637 | 0.002951 |
| too_easy | php_exit_single | 7 | 0.00201686 | 0.001571 |
| too_easy | random_3sat_control | 14 | 0.0119841 | 0.006142 |
| too_easy | subset_cardinality | 5 | 0.006088 | 0.005883 |
| too_easy | tseitin_complete | 4 | 0.0098515 | 0.008477 |
| too_hard_above_target | vertex_cover_torus | 1 | 10.0007 | 10.0007 |

## Target Bases

| family | base_instance_id | expected_result | num_vars | num_clauses | plain_glucose_result | plain_glucose_cpu_time | plain_glucose_decisions | plain_glucose_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k8_color7 | UNSATISFIABLE | 56 | 372 | UNSATISFIABLE | 0.051891 | 7227 | 6460 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | UNKNOWN | 160 | 704 | UNSATISFIABLE | 0.053728 | 6229 | 5335 |
| tseitin_complete | tseitin_k7_odd | UNSATISFIABLE | 21 | 224 | UNSATISFIABLE | 0.074278 | 29623 | 21872 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | UNKNOWN | 18 | 8586 | SATISFIABLE | 0.128188 | 7 | 0 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | UNKNOWN | 180 | 760 | SATISFIABLE | 0.132388 | 7690 | 6573 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | UNKNOWN | 220 | 928 | SATISFIABLE | 0.158679 | 13323 | 11224 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | UNKNOWN | 220 | 942 | UNSATISFIABLE | 0.661994 | 33452 | 29018 |
| complete_coloring | k9_color8 | UNSATISFIABLE | 72 | 549 | UNSATISFIABLE | 1.03784 | 54148 | 49327 |
| php | php_p9_h8 | UNSATISFIABLE | 72 | 549 | UNSATISFIABLE | 1.05591 | 49178 | 44861 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | UNKNOWN | 260 | 1097 | SATISFIABLE | 1.1704 | 41915 | 35659 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | UNKNOWN | 300 | 1266 | SATISFIABLE | 1.19163 | 47433 | 39846 |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | UNSATISFIABLE | 18 | 31860 | UNSATISFIABLE | 1.32549 | 11 | 12 |
| dominating_set_hex | dominating_set_hex_5x4_s5 | UNKNOWN | 20 | 38780 | SATISFIABLE | 2.20773 | 8 | 0 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | UNKNOWN | 20 | 38780 | SATISFIABLE | 2.32357 | 8 | 0 |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | UNSATISFIABLE | 18 | 43794 | UNSATISFIABLE | 2.84404 | 16 | 17 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | UNKNOWN | 260 | 1113 | UNSATISFIABLE | 4.64227 | 167986 | 145890 |
| dominating_set_hex | dominating_set_hex_3x7_s5 | UNKNOWN | 21 | 54285 | SATISFIABLE | 5.17781 | 12 | 0 |
| complete_coloring | k10_color9 | UNSATISFIABLE | 90 | 775 | UNSATISFIABLE | 6.88808 | 604963 | 534806 |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | UNSATISFIABLE | 20 | 77560 | UNSATISFIABLE | 7.00154 | 11 | 12 |
| php | php_p10_h9 | UNSATISFIABLE | 90 | 775 | UNSATISFIABLE | 8.0667 | 734102 | 641326 |
