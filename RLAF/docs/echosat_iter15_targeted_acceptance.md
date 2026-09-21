# EchoSAT iter=15 Targeted Acceptance

This freezes v1.2 `iter=15.pt` as the main candidate and compares it against v1.2 `best.pt`, v1.2 `iter=235.pt`, v1.1 `iter=85.pt`, and v1.2 `iter=50.pt` as a wc3 diagnostic. It does not train, expand the benchmark, or add a gate/selector.

## Artifacts

- observations: `runs/analysis/echosat_iter15_targeted_acceptance_observations.csv`
- strict acceptance: `runs/analysis/echosat_iter15_targeted_acceptance_strict_acceptance.csv`
- summary by base: `runs/analysis/echosat_iter15_targeted_acceptance_by_base.csv`
- summary by family: `runs/analysis/echosat_iter15_targeted_acceptance_by_family.csv`
- main candidate checks: `runs/analysis/echosat_iter15_targeted_acceptance_main_candidate_checks.csv`

## Scope

- observation rows: `2025`
- families: `complete_coloring`, `php`, `subset_cardinality`, `random_3sat_control`
- primary acceptance budget: `wc1`
- diagnostic budgets: `wc3`, `wc5`
- success metric: adapter-vs-cached decisions/conflicts reduction; CPU is diagnostic only.

## Acceptance

- main candidate wc1 acceptance: `PASS`

| check | passed |
| --- | --- |
| k9_color8_wc1_search_ok_is_1 | True |
| php_p9_h8_wc1_search_ok_is_1 | True |
| k10_color9_wc1_search_ok_at_least_2_of_3 | True |
| php_p10_h9_wc1_search_ok_at_least_2_of_3 | True |
| random_control_wc1_search_ok_near_zero | True |
| subset_bw12_perm1730_remains_negative | True |
| all_event_adapter_solved | True |
| known_expected_all_match | True |
| MAIN_CANDIDATE_WC1_ACCEPTANCE | True |

## Strict Search-Work Scores

| candidate_label | candidate_name | candidate_role | warmup_conflicts | strict_search_work_score | anchor_min_search_ok_frac | hard_recovery_min_search_ok_frac | strong_symmetry_search_ok_frac | random_control_search_ok_frac | subset_bw12_perm1730_search_ok_frac | overall_search_blowup_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_2_iter15 | v1.2 iter=15.pt | main_candidate | 1 | 4.42222 | 1 | 0.666667 | 0.8 | 0 | 0 | 0.711111 |
| v1_1_iter85 | v1.1 iter=85.pt | control | 1 | 4.34921 | 1 | 0.666667 | 0.8 | 0.047619 | 0 | 0.688889 |
| v1_2_iter235 | v1.2 iter=235.pt | control | 1 | 4.13651 | 1 | 0.666667 | 0.733333 | 0.142857 | 0 | 0.644444 |
| v1_2_best | v1.2 best.pt | control | 1 | 3.66667 | 1 | 0.333333 | 0.733333 | 0 | 0 | 0.733333 |
| v1_2_iter50 | v1.2 iter=50.pt | wc3_diagnostic | 1 | 2.2381 | 0.666667 | 0.333333 | 0.466667 | 0.047619 | 0 | 0.8 |
| v1_2_iter50 | v1.2 iter=50.pt | wc3_diagnostic | 3 | 3.33651 | 1 | 0.333333 | 0.666667 | 0.142857 | 0 | 0.711111 |
| v1_2_iter235 | v1.2 iter=235.pt | control | 3 | 2.69206 | 1 | 0 | 0.666667 | 0.142857 | 0 | 0.688889 |
| v1_2_best | v1.2 best.pt | control | 3 | 2.60317 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.711111 |
| v1_2_iter15 | v1.2 iter=15.pt | main_candidate | 3 | 2.60317 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.711111 |
| v1_1_iter85 | v1.1 iter=85.pt | control | 3 | 2.51429 | 1 | 0 | 0.533333 | 0.142857 | 0 | 0.733333 |
| v1_2_iter15 | v1.2 iter=15.pt | main_candidate | 5 | 2.64762 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.666667 |
| v1_1_iter85 | v1.1 iter=85.pt | control | 5 | 2.6254 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.688889 |
| v1_2_best | v1.2 best.pt | control | 5 | 2.6254 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.688889 |
| v1_2_iter50 | v1.2 iter=50.pt | wc3_diagnostic | 5 | 2.60317 | 1 | 0 | 0.6 | 0.142857 | 0 | 0.711111 |
| v1_2_iter235 | v1.2 iter=235.pt | control | 5 | 2.53651 | 1 | 0 | 0.533333 | 0.142857 | 0 | 0.711111 |

## Focus Bases

| candidate_label | candidate_role | warmup_conflicts | family | base_instance_id | search_ok_frac | search_blowup_frac | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_cpu_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_1_iter85 | control | 1 | complete_coloring | k10_color9 | 0.666667 | 0.333333 | -14908.3 | -13513.3 | -0.342062 | -0.585491 |
| v1_2_best | control | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 10846 | 11323.3 | 0.0700367 | -0.200956 |
| v1_2_iter235 | control | 1 | complete_coloring | k10_color9 | 0.666667 | 0.333333 | 4412.33 | 4814.33 | -0.0381189 | -0.291214 |
| v1_2_iter15 | main_candidate | 1 | complete_coloring | k10_color9 | 0.666667 | 0.333333 | -19274 | -15695.7 | -0.129494 | -0.373975 |
| v1_2_iter50 | wc3_diagnostic | 1 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 9638.67 | 11185.3 | 0.0730211 | -0.188496 |
| v1_1_iter85 | control | 1 | complete_coloring | k9_color8 | 1 | 0 | -3761 | -3397.67 | -0.0980327 | 0.0518264 |
| v1_2_best | control | 1 | complete_coloring | k9_color8 | 1 | 0 | -6155.67 | -5800 | -0.146323 | 0.0297852 |
| v1_2_iter235 | control | 1 | complete_coloring | k9_color8 | 1 | 0 | -3511.33 | -3194.67 | -0.111031 | 0.0429839 |
| v1_2_iter15 | main_candidate | 1 | complete_coloring | k9_color8 | 1 | 0 | -1917.67 | -1785 | -0.0965999 | 0.0365222 |
| v1_2_iter50 | wc3_diagnostic | 1 | complete_coloring | k9_color8 | 0.666667 | 0.333333 | -4444.33 | -4098.67 | -0.117039 | 0.0363143 |
| v1_1_iter85 | control | 1 | php | php_p10_h9 | 0.666667 | 0.333333 | -9525 | -8561.33 | -0.293576 | -0.563826 |
| v1_2_best | control | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | 10846 | 11323.3 | 0.0446589 | -0.20612 |
| v1_2_iter235 | control | 1 | php | php_p10_h9 | 0.666667 | 0.333333 | 4412.33 | 4814.33 | -0.0146011 | -0.312098 |
| v1_2_iter15 | main_candidate | 1 | php | php_p10_h9 | 0.666667 | 0.333333 | -29556.7 | -25850.3 | -0.257812 | -0.571485 |
| v1_2_iter50 | wc3_diagnostic | 1 | php | php_p10_h9 | 0.333333 | 0.666667 | 14540.3 | 16093 | 0.180474 | -0.0929171 |
| v1_1_iter85 | control | 1 | php | php_p9_h8 | 1 | 0 | -4223 | -3825 | -0.0992062 | 0.0477992 |
| v1_2_best | control | 1 | php | php_p9_h8 | 1 | 0 | -5994.67 | -5686 | -0.137673 | 0.00804086 |
| v1_2_iter235 | control | 1 | php | php_p9_h8 | 1 | 0 | -3511.33 | -3194.67 | -0.100826 | 0.0363108 |
| v1_2_iter15 | main_candidate | 1 | php | php_p9_h8 | 1 | 0 | -1917.67 | -1785 | -0.0907354 | 0.0275715 |
| v1_2_iter50 | wc3_diagnostic | 1 | php | php_p9_h8 | 0.666667 | 0.333333 | -4444.33 | -4098.67 | -0.109924 | 0.0271327 |
| v1_1_iter85 | control | 1 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 22 | 21.6667 | -0.000455333 | 0.0539464 |
| v1_2_best | control | 1 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 30 | 26 | -0.000395444 | 0.0604351 |
| v1_2_iter235 | control | 1 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 25.3333 | 19.3333 | 0.000930778 | 0.0627065 |
| v1_2_iter15 | main_candidate | 1 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 26.3333 | 25 | -0.000596444 | 0.0512747 |
| v1_2_iter50 | wc3_diagnostic | 1 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 11.6667 | 14.3333 | -0.000496778 | 0.0571729 |
| v1_1_iter85 | control | 3 | complete_coloring | k10_color9 | 0 | 1 | 80229.3 | 76808.7 | 0.201366 | -0.0862847 |
| v1_2_best | control | 3 | complete_coloring | k10_color9 | 0 | 1 | 83745.7 | 81021 | 0.24617 | -0.0133195 |
| v1_2_iter235 | control | 3 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 56748 | 54870.3 | 0.0378567 | -0.235486 |
| v1_2_iter15 | main_candidate | 3 | complete_coloring | k10_color9 | 0 | 1 | 91650.3 | 87512 | 0.412336 | 0.120666 |
| v1_2_iter50 | wc3_diagnostic | 3 | complete_coloring | k10_color9 | 0.333333 | 0.666667 | 41945.7 | 41556.7 | -0.0674878 | -0.305297 |
| v1_1_iter85 | control | 3 | complete_coloring | k9_color8 | 1 | 0 | -4223.67 | -3865 | -0.150584 | -0.00551573 |
| v1_2_best | control | 3 | complete_coloring | k9_color8 | 1 | 0 | -3847.33 | -3551.33 | -0.166342 | -0.023216 |
| v1_2_iter235 | control | 3 | complete_coloring | k9_color8 | 1 | 0 | -3125.33 | -2785.33 | -0.148177 | 0.0122514 |
| v1_2_iter15 | main_candidate | 3 | complete_coloring | k9_color8 | 1 | 0 | -3126.33 | -2760.33 | -0.146207 | 0.00511542 |
| v1_2_iter50 | wc3_diagnostic | 3 | complete_coloring | k9_color8 | 1 | 0 | -3953 | -3570 | -0.150623 | 0.00134076 |
| v1_1_iter85 | control | 3 | php | php_p10_h9 | 0 | 1 | 80229.3 | 76808.7 | 0.201266 | -0.0688438 |
| v1_2_best | control | 3 | php | php_p10_h9 | 0 | 1 | 83745.7 | 81021 | 0.278329 | -0.0165928 |
| v1_2_iter235 | control | 3 | php | php_p10_h9 | 0 | 1 | 69020.3 | 66389.3 | 0.125213 | -0.139528 |
| v1_2_iter15 | main_candidate | 3 | php | php_p10_h9 | 0 | 1 | 91650.3 | 87512 | 0.405904 | 0.145768 |
| v1_2_iter50 | wc3_diagnostic | 3 | php | php_p10_h9 | 0.333333 | 0.666667 | 41945.7 | 41556.7 | -0.0731389 | -0.36912 |
| v1_1_iter85 | control | 3 | php | php_p9_h8 | 1 | 0 | -4223.67 | -3865 | -0.144494 | -0.00463334 |
| v1_2_best | control | 3 | php | php_p9_h8 | 1 | 0 | -3847.33 | -3551.33 | -0.1585 | -0.0219101 |
| v1_2_iter235 | control | 3 | php | php_p9_h8 | 1 | 0 | -3125.33 | -2785.33 | -0.1414 | -0.00324629 |
| v1_2_iter15 | main_candidate | 3 | php | php_p9_h8 | 1 | 0 | -3126.33 | -2760.33 | -0.130011 | 0.0148174 |
| v1_2_iter50 | wc3_diagnostic | 3 | php | php_p9_h8 | 1 | 0 | -3953 | -3570 | -0.139236 | -0.00732265 |
| v1_1_iter85 | control | 3 | subset_cardinality | subset_cardinality_bw12 | 0.333333 | 0.666667 | 18.6667 | -0.333333 | 0.000566333 | 0.0606425 |
| v1_2_best | control | 3 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 27.3333 | 14 | 0.000543556 | 0.0579183 |
| v1_2_iter235 | control | 3 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 15 | 10.6667 | 0.000420889 | 0.0568948 |
| v1_2_iter15 | main_candidate | 3 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 26.6667 | 12.6667 | 0.00122967 | 0.0626363 |
| v1_2_iter50 | wc3_diagnostic | 3 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 19 | 9.33333 | 0.000621556 | 0.0590644 |
| v1_1_iter85 | control | 5 | complete_coloring | k10_color9 | 0 | 1 | 44963.3 | 44142 | -0.0372144 | -0.259935 |
| v1_2_best | control | 5 | complete_coloring | k10_color9 | 0 | 1 | 57494 | 55552 | 0.103966 | -0.13732 |
| v1_2_iter235 | control | 5 | complete_coloring | k10_color9 | 0 | 1 | 75616.3 | 71580.7 | 0.157251 | -0.106799 |
| v1_2_iter15 | main_candidate | 5 | complete_coloring | k10_color9 | 0 | 1 | 114125 | 107781 | 0.481271 | 0.242355 |
| v1_2_iter50 | wc3_diagnostic | 5 | complete_coloring | k10_color9 | 0 | 1 | 82627 | 79099.7 | 0.308989 | 0.0342163 |
| v1_1_iter85 | control | 5 | complete_coloring | k9_color8 | 1 | 0 | -5786.67 | -5441.33 | -0.166779 | -0.0140292 |
| v1_2_best | control | 5 | complete_coloring | k9_color8 | 1 | 0 | -3867.33 | -3782.67 | -0.169321 | -0.0224591 |
| v1_2_iter235 | control | 5 | complete_coloring | k9_color8 | 1 | 0 | -4227.67 | -4061 | -0.174966 | -0.0137251 |
| v1_2_iter15 | main_candidate | 5 | complete_coloring | k9_color8 | 1 | 0 | -4872.67 | -4634.67 | -0.158358 | -0.00267039 |
| v1_2_iter50 | wc3_diagnostic | 5 | complete_coloring | k9_color8 | 1 | 0 | -4414.33 | -4202.33 | -0.168651 | -0.0159586 |
| v1_1_iter85 | control | 5 | php | php_p10_h9 | 0 | 1 | 44963.3 | 44142 | -0.0206867 | -0.299689 |
| v1_2_best | control | 5 | php | php_p10_h9 | 0 | 1 | 67641.7 | 64749.7 | 0.157946 | -0.122605 |
| v1_2_iter235 | control | 5 | php | php_p10_h9 | 0 | 1 | 79329 | 74741.7 | 0.17535 | -0.103436 |
| v1_2_iter15 | main_candidate | 5 | php | php_p10_h9 | 0 | 1 | 114125 | 107781 | 0.529559 | 0.261276 |
| v1_2_iter50 | wc3_diagnostic | 5 | php | php_p10_h9 | 0 | 1 | 82934 | 79422.3 | 0.301788 | 0.0250316 |
| v1_1_iter85 | control | 5 | php | php_p9_h8 | 1 | 0 | -5786.67 | -5441.33 | -0.162486 | -0.0396517 |
| v1_2_best | control | 5 | php | php_p9_h8 | 1 | 0 | -3867.33 | -3782.67 | -0.163121 | -0.0286284 |
| v1_2_iter235 | control | 5 | php | php_p9_h8 | 1 | 0 | -4227.67 | -4061 | -0.164116 | -0.0296462 |
| v1_2_iter15 | main_candidate | 5 | php | php_p9_h8 | 1 | 0 | -4872.67 | -4634.67 | -0.159236 | -0.025727 |
| v1_2_iter50 | wc3_diagnostic | 5 | php | php_p9_h8 | 1 | 0 | -4414.33 | -4202.33 | -0.157971 | -0.0293713 |
| v1_1_iter85 | control | 5 | subset_cardinality | subset_cardinality_bw12 | 0.333333 | 0.666667 | 8.66667 | 11 | -0.000402222 | 0.0643888 |
| v1_2_best | control | 5 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 19 | 21.6667 | -0.000157 | 0.0578814 |
| v1_2_iter235 | control | 5 | subset_cardinality | subset_cardinality_bw12 | 0.333333 | 0.666667 | 12 | 17 | -0.00128456 | 0.0722407 |
| v1_2_iter15 | main_candidate | 5 | subset_cardinality | subset_cardinality_bw12 | 0.333333 | 0.666667 | 6.33333 | 8 | -0.000515222 | 0.0583758 |
| v1_2_iter50 | wc3_diagnostic | 5 | subset_cardinality | subset_cardinality_bw12 | 0 | 1 | 17.3333 | 17 | 0.000728333 | 0.0581288 |

## Random Controls

| candidate_label | candidate_role | warmup_conflicts | search_ok_frac | search_blowup_frac | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_cpu_delta_mean | adapter_plain_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_1_iter85 | control | 1 | 0.047619 | 0.952381 | 17021.4 | 14166.2 | 0.180273 | -0.455362 |
| v1_2_best | control | 1 | 0 | 1 | 17402.8 | 14577.1 | 0.181616 | -0.454247 |
| v1_2_iter235 | control | 1 | 0.142857 | 0.857143 | 10505.4 | 8364.33 | 0.085929 | -0.560123 |
| v1_2_iter15 | main_candidate | 1 | 0 | 1 | 20978.8 | 17762 | 0.251466 | -0.417188 |
| v1_2_iter50 | wc3_diagnostic | 1 | 0.047619 | 0.952381 | 15941 | 13253.3 | 0.142559 | -0.491359 |
| v1_1_iter85 | control | 3 | 0.142857 | 0.857143 | 11402.3 | 9190.95 | 0.10064 | -0.532602 |
| v1_2_best | control | 3 | 0.142857 | 0.857143 | 11759.8 | 9524.48 | 0.0853258 | -0.572632 |
| v1_2_iter235 | control | 3 | 0.142857 | 0.857143 | 8362 | 6628.19 | 0.0451569 | -0.599733 |
| v1_2_iter15 | main_candidate | 3 | 0.142857 | 0.857143 | 11126.9 | 8959.24 | 0.0737863 | -0.554278 |
| v1_2_iter50 | wc3_diagnostic | 3 | 0.142857 | 0.857143 | 11195.1 | 9033.52 | 0.0946598 | -0.542339 |
| v1_1_iter85 | control | 5 | 0.142857 | 0.857143 | 8828.24 | 6926.71 | 0.0324751 | -0.597043 |
| v1_2_best | control | 5 | 0.142857 | 0.857143 | 9114.81 | 7212.95 | 0.0493291 | -0.592155 |
| v1_2_iter235 | control | 5 | 0.142857 | 0.857143 | 9232.57 | 7401.67 | 0.0605525 | -0.582091 |
| v1_2_iter15 | main_candidate | 5 | 0.142857 | 0.857143 | 8614.81 | 6741 | 0.0485398 | -0.590173 |
| v1_2_iter50 | wc3_diagnostic | 5 | 0.142857 | 0.857143 | 9435.33 | 7475.14 | 0.0777091 | -0.568597 |

## Interpretation

- `v1_2_iter15` is accepted only on wc1; wc3/wc5 are diagnostics for warmup sensitivity.
- `v1_2_iter50` remains a wc3 diagnostic and is not promoted to the main candidate.
- Protocol time and adapter-vs-plain deltas are recorded, but they do not define success here.
- No solver speedup claim follows from this targeted acceptance report.
