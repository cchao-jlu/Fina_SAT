# EchoSAT Symmetry GRPO v1.8 Reward Replay Dry-Run

This is an offline objective-repair dry-run over existing v1.7 reward replay rows. It does not rerun solvers, train a checkpoint, expand the benchmark, or add a gate/selector.

v1.8 keeps the strict search-work lens: a row may carry positive training advantage only when adapter-vs-cached decisions and conflicts both improve and the row is not a random control, protected subset failure, anchor/hard-negative failure, weighted-risk row, near-cap row, CPU-only win, or result mismatch.

The `grpo_raw_advantage_unclamped` column remains a diagnostic group-normalization value. The hard requirement here is that the training-visible `grpo_raw_advantage` and `grpo_final_advantage` are non-positive on blocked rows.

## Inputs

- v1.7 replay rows: `runs/analysis/echosat_symmetry_grpo_v1_7_reward_replay_dryrun_rows.csv`

## Outputs

- rows: `runs/analysis/echosat_symmetry_grpo_v1_8_reward_replay_dryrun_rows.csv`
- role summary: `runs/analysis/echosat_symmetry_grpo_v1_8_reward_replay_dryrun_role_summary.csv`
- base summary: `runs/analysis/echosat_symmetry_grpo_v1_8_reward_replay_dryrun_base_summary.csv`
- checks: `runs/analysis/echosat_symmetry_grpo_v1_8_reward_replay_dryrun_checks.csv`

## Scope

- rows: `129312`
- roles: `anchor, anchor_failure, hard_negative, hard_negative_failure, other, random_control, subset_failure`
- dry-run pass: `True`

## Checks

| check | passed | evidence |
| --- | --- | --- |
| anchor_final_positive_recovered | True | anchor positive rows=14932 |
| hard_negative_final_positive_recovered | True | hard_negative positive rows=9367 |
| hard_negative_final_pressure_not_weaker_than_v1_7 | True | v18_mean=0.657095 v17_mean=0.51943 |
| random_control_no_raw_or_final_positive | True | raw_pos=0 final_pos=0 |
| subset_failure_no_raw_or_final_positive | True | raw_pos=0 final_pos=0 |
| anchor_failure_no_raw_or_final_positive | True | raw_pos=0 final_pos=0 |
| hard_negative_failure_no_raw_or_final_positive | True | raw_pos=0 final_pos=0 |
| blocked_rows_no_raw_or_final_positive | True | blocked=95642 raw_pos=0 final_pos=0 |
| cpu_only_search_bad_no_raw_or_final_positive | True | cpu_only=0 raw_pos=0 final_pos=0 |
| weighted_risk_no_raw_or_final_positive | True | weighted_risk=31380 raw_pos=0 final_pos=0 |
| near_cap_no_raw_or_final_positive | True | near_cap=2914 raw_pos=0 final_pos=0 |
| subset_bw12_perm1730_no_raw_or_final_positive | True | rows=1344 raw_pos=0 final_pos=0 |
| positive_allowed_not_all_zero | True | nonblocked_final_pos=26579 |
| ALL_V1_8_DRYRUN_CHECKS | True | aggregate of preceding checks |

## Role Summary

| echosat_replay_role | echosat_search_ok | echosat_search_blowup | echosat_positive_allowed | echosat_v18_blocked_positive_signal | echosat_v18_cpu_only_search_bad | echosat_v18_weighted_risk_blocked | echosat_v18_near_cap_blocked | echosat_v18_unclamped_positive_blocked | echosat_v18_hard_negative_pressure | echosat_symmetry_reward | echosat_cost | grpo_raw_advantage_unclamped | v17_grpo_raw_advantage | grpo_raw_advantage | v17_grpo_final_advantage | grpo_final_advantage | grpo_positive_raw_advantage_clamped | grpo_positive_advantage_clamped | rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchor | 1 | 0 | 0.982968 | 0.017032 | 0 | 0.017032 | 0 | 0.011551 | 0 | 0.104192 | 0.053341 | 0.175406 | 0.175406 | 0.168468 | 0.166956 | 0.166956 | 0.011551 | 0 | 22076 |
| anchor_failure | 0 | 0.999554 | 0 | 1 | 0 | 0.016057 | 0 | 0.28033 | 0 | 0 | 182.015 | -0.863572 | -1.00862 | -1.00862 | -0.99957 | -0.99957 | 0 | 0 | 4484 |
| hard_negative | 1 | 0 | 0.867431 | 0.132569 | 0 | 0.132569 | 0 | 0.126147 | 0.021609 | 0.107188 | 349.854 | 0.697836 | 0.697836 | 0.746487 | 0.51943 | 0.657095 | 0.126147 | 0 | 10900 |
| hard_negative_failure | 0 | 0.995466 | 0 | 1 | 0 | 0.198004 | 0.000294 | 0.446443 | 0 | 0 | 839.79 | -0.223955 | -0.508461 | -0.508461 | -0.404884 | -0.404884 | 0 | 0 | 33964 |
| other | 0.144919 | 0.393939 | 0.082125 | 0.917875 | 0 | 0.438349 | 0.088819 | 0.495657 | 0 | 0.008261 | 886.057 | -0 | -0 | -0.336579 | -0.274421 | -0.274421 | 0.495657 | 0 | 30624 |
| random_control | 0.196181 | 0.61088 | 0 | 1 | 0 | 0.342361 | 0.007099 | 0.52936 | 0 | 0 | 1309.76 | -0 | -0.3901 | -0.3901 | -0.3901 | -0.3901 | 0 | 0 | 25920 |
| subset_failure | 0.001488 | 0.997768 | 0 | 1 | 0 | 0.345238 | 0 | 0.505208 | 0 | 0 | 1428.21 | 0 | -0.392999 | -0.392999 | -0.232695 | -0.232695 | 0 | 0 | 1344 |

## Priority Base Summary

| echosat_replay_role | family | base_instance_id | echosat_search_ok | echosat_search_blowup | echosat_positive_allowed | echosat_v18_blocked_positive_signal | echosat_v18_cpu_only_search_bad | echosat_v18_weighted_risk_blocked | echosat_v18_near_cap_blocked | echosat_v18_unclamped_positive_blocked | echosat_v18_hard_negative_pressure | echosat_symmetry_reward | echosat_cost | grpo_raw_advantage_unclamped | v17_grpo_raw_advantage | grpo_raw_advantage | v17_grpo_final_advantage | grpo_final_advantage | grpo_positive_raw_advantage_clamped | grpo_positive_advantage_clamped | rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchor | complete_coloring | k9_color8 | 1 | 0 | 0.988132 | 0.011868 | 0 | 0.011868 | 0 | 0.00774 | 0 | 0.116077 | -0.018163 | 0.081583 | 0.081583 | 0.07681 | 0.076121 | 0.076121 | 0.00774 | 0 | 3876 |
| anchor | php | php_p9_h8 | 1 | 0 | 0.981868 | 0.018132 | 0 | 0.018132 | 0 | 0.012363 | 0 | 0.101661 | 0.068569 | 0.195387 | 0.195387 | 0.187988 | 0.186301 | 0.186301 | 0.012363 | 0 | 18200 |
| anchor_failure | complete_coloring | k9_color8 | 0 | 1 | 0 | 1 | 0 | 0.018519 | 0 | 0 | 0 | 0 | 56.5429 | -2.92791 | -2.92791 | -2.92791 | -2.90166 | -2.90166 | 0 | 0 | 108 |
| anchor_failure | php | php_p9_h8 | 0 | 0.999543 | 0 | 1 | 0 | 0.015996 | 0 | 0.287249 | 0 | 0 | 185.112 | -0.812624 | -0.96125 | -0.96125 | -0.952627 | -0.952627 | 0 | 0 | 4376 |
| hard_negative | complete_coloring | k10_color9 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0.02609 | 0.129509 | -0.093743 | 0.654871 | 0.654871 | 0.818589 | 0.650158 | 0.812698 | 0 | 0 | 968 |
| hard_negative | php | php_p10_h9 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0.027751 | 0.137757 | -0.100151 | 0.612305 | 0.612305 | 0.777453 | 0.607904 | 0.771864 | 0 | 0 | 6506 |
| hard_negative | subset_cardinality | subset_cardinality_bw12 | 1 | 0 | 0.578225 | 0.421775 | 0 | 0.421775 | 0 | 0.401343 | 0.008679 | 0.042832 | 1113.3 | 0.8724 | 0.8724 | 0.667311 | 0.31448 | 0.395184 | 0.401343 | 0 | 3426 |
| hard_negative_failure | complete_coloring | k10_color9 | 0 | 1 | 0 | 1 | 0 | 0.001577 | 0.001577 | 0.45623 | 0 | 0 | 463.812 | -0.249967 | -0.527094 | -0.527094 | -0.523302 | -0.523302 | 0 | 0 | 2536 |
| hard_negative_failure | php | php_p10_h9 | 0 | 1 | 0 | 1 | 0 | 0.000449 | 0.000449 | 0.435356 | 0 | 0 | 501.225 | -0.298401 | -0.558917 | -0.558917 | -0.554898 | -0.554898 | 0 | 0 | 13350 |
| hard_negative_failure | subset_cardinality | subset_cardinality_bw12 | 0 | 0.991481 | 0 | 1 | 0 | 0.371446 | 0 | 0.453258 | 0 | 0 | 1142.55 | -0.16533 | -0.468587 | -0.468587 | -0.277493 | -0.277493 | 0 | 0 | 18078 |
| random_control | random_3sat_control | random_3sat_control_v100_c360_seed1931 | 0.884559 | 0.072059 | 0 | 1 | 0 | 0.447059 | 0 | 0.536765 | 0 | 0 | 918.185 | 0 | -0.364264 | -0.364264 | -0.364264 | -0.364264 | 0 | 0 | 1360 |
| random_control | random_3sat_control | random_3sat_control_v100_c425_seed1932 | 0.836765 | 0.158824 | 0 | 1 | 0 | 0.211765 | 0 | 0.568382 | 0 | 0 | 48.844 | -0 | -0.379659 | -0.379659 | -0.379659 | -0.379659 | 0 | 0 | 1360 |
| random_control | random_3sat_control | random_3sat_control_v100_c600_seed1914 | 0 | 1 | 0 | 1 | 0 | 0.323529 | 0 | 0.409926 | 0 | 0 | 79.124 | -0 | -0.383257 | -0.383257 | -0.383257 | -0.383257 | 0 | 0 | 544 |
| random_control | random_3sat_control | random_3sat_control_v140_c595_seed1935 | 0.001838 | 0.998162 | 0 | 1 | 0 | 0.132353 | 0 | 0.500919 | 0 | 0 | 85.1092 | -0 | -0.395324 | -0.395324 | -0.395324 | -0.395324 | 0 | 0 | 1088 |
| random_control | random_3sat_control | random_3sat_control_v150_c525_seed1936 | 0.477941 | 0.441176 | 0 | 1 | 0 | 0.411765 | 0 | 0.6875 | 0 | 0 | 80.9286 | -0 | -0.33668 | -0.33668 | -0.33668 | -0.33668 | 0 | 0 | 272 |
| random_control | random_3sat_control | random_3sat_control_v150_c638_seed1937 | 0.32598 | 0.666667 | 0 | 1 | 0 | 0 | 0 | 0.596814 | 0 | 0 | 157.732 | 0 | -0.420018 | -0.420018 | -0.420018 | -0.420018 | 0 | 0 | 816 |
| random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 0.0125 | 0.9875 | 0 | 1 | 0 | 0 | 0 | 0.5125 | 0 | 0 | 74.3474 | 0 | -0.391367 | -0.391367 | -0.391367 | -0.391367 | 0 | 0 | 240 |
| random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.534722 | 0 | 0 | 67.5147 | -0 | -0.389773 | -0.389773 | -0.389773 | -0.389773 | 0 | 0 | 144 |
| random_control | random_3sat_control | random_3sat_control_v20_c85_seed1901 | 0 | 0.658088 | 0 | 1 | 0 | 0.323529 | 0 | 0.500919 | 0 | 0 | 2408.62 | -0 | -0.398378 | -0.398378 | -0.398378 | -0.398378 | 0 | 0 | 1088 |
| random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.491667 | 0 | 0 | 67.7202 | -0 | -0.386809 | -0.386809 | -0.386809 | -0.386809 | 0 | 0 | 240 |
| random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.583333 | 0 | 0 | 48.5343 | 0 | -0.397245 | -0.397245 | -0.397245 | -0.397245 | 0 | 0 | 192 |
| random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 0.580357 | 0.419643 | 0 | 1 | 0 | 0.416667 | 0.125 | 0.675595 | 0 | 0 | 163.291 | -0 | -0.422191 | -0.422191 | -0.422191 | -0.422191 | 0 | 0 | 336 |
| random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 0 | 1 | 0 | 1 | 0 | 0.986111 | 0.986111 | 0.576389 | 0 | 0 | 45.0676 | -0 | -0.363953 | -0.363953 | -0.363953 | -0.363953 | 0 | 0 | 144 |
| random_control | random_3sat_control | random_3sat_control_v28_c119_seed1922 | 0.11292 | 0.096639 | 0 | 1 | 0 | 0.386555 | 0 | 0.61187 | 0 | 0 | 2051.29 | 0 | -0.37162 | -0.37162 | -0.37162 | -0.37162 | 0 | 0 | 1904 |
| random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.4375 | 0 | 0 | 68.5519 | 0 | -0.37745 | -0.37745 | -0.37745 | -0.37745 | 0 | 0 | 144 |
| random_control | random_3sat_control | random_3sat_control_v30_c128_seed1902 | 0.321078 | 0.389706 | 0 | 1 | 0 | 0.411765 | 0 | 0.519608 | 0 | 0 | 2346.65 | 0 | -0.392213 | -0.392213 | -0.392213 | -0.392213 | 0 | 0 | 816 |
| random_control | random_3sat_control | random_3sat_control_v32_c136_seed1923 | 0 | 0.242647 | 0 | 1 | 0 | 0.313725 | 0 | 0.513889 | 0 | 0 | 2428.6 | -0 | -0.394928 | -0.394928 | -0.394928 | -0.394928 | 0 | 0 | 2448 |
| random_control | random_3sat_control | random_3sat_control_v35_c149_seed1911 | 0.045956 | 0.887868 | 0 | 1 | 0 | 0.5 | 0 | 0.518382 | 0 | 0 | 2902.56 | 0 | -0.423466 | -0.423466 | -0.423466 | -0.423466 | 0 | 0 | 544 |
| random_control | random_3sat_control | random_3sat_control_v40_c170_seed1903 | 0 | 0.932598 | 0 | 1 | 0 | 0.385621 | 0 | 0.550654 | 0 | 0 | 1606.82 | 0 | -0.39252 | -0.39252 | -0.39252 | -0.39252 | 0 | 0 | 2448 |
| random_control | random_3sat_control | random_3sat_control_v45_c191_seed1924 | 0.003676 | 0.984681 | 0 | 1 | 0 | 0.362745 | 0 | 0.528186 | 0 | 0 | 2116.59 | 0 | -0.418402 | -0.418402 | -0.418402 | -0.418402 | 0 | 0 | 1632 |
| random_control | random_3sat_control | random_3sat_control_v50_c213_seed1925 | 1 | 0 | 0 | 1 | 0 | 0.4 | 0 | 0.502206 | 0 | 0 | 1478.12 | -0 | -0.394605 | -0.394605 | -0.394605 | -0.394605 | 0 | 0 | 1360 |
| random_control | random_3sat_control | random_3sat_control_v60_c180_seed1912 | 0.137868 | 0.794118 | 0 | 1 | 0 | 0.431373 | 0 | 0.560662 | 0 | 0 | 2101.46 | 0 | -0.402117 | -0.402117 | -0.402117 | -0.402117 | 0 | 0 | 1632 |
| random_control | random_3sat_control | random_3sat_control_v60_c255_seed1927 | 0.000735 | 0.999265 | 0 | 1 | 0 | 0.4 | 0 | 0.347059 | 0 | 0 | 572.515 | 0 | -0.354099 | -0.354099 | -0.354099 | -0.354099 | 0 | 0 | 1360 |
| random_control | random_3sat_control | random_3sat_control_v80_c260_seed1929 | 0 | 0.776838 | 0 | 1 | 0 | 0.423529 | 0 | 0.522426 | 0 | 0 | 776.24 | -0 | -0.385675 | -0.385675 | -0.385675 | -0.385675 | 0 | 0 | 2720 |
| random_control | random_3sat_control | random_3sat_control_v80_c340_seed1913 | 0 | 1 | 0 | 1 | 0 | 0.176471 | 0 | 0.584559 | 0 | 0 | 54.1673 | 0 | -0.401734 | -0.401734 | -0.401734 | -0.401734 | 0 | 0 | 272 |
| random_control | random_3sat_control | random_3sat_control_v90_c383_seed1930 | 0.066176 | 0.930147 | 0 | 1 | 0 | 0.333333 | 0 | 0.53799 | 0 | 0 | 644.057 | 0 | -0.39735 | -0.39735 | -0.39735 | -0.39735 | 0 | 0 | 816 |
| subset_failure | subset_cardinality | subset_cardinality_bw12 | 0.001488 | 0.997768 | 0 | 1 | 0 | 0.345238 | 0 | 0.505208 | 0 | 0 | 1428.21 | 0 | -0.392999 | -0.392999 | -0.232695 | -0.232695 | 0 | 0 | 1344 |

## Conclusion

- If these checks pass, the v1.8 objective is ready to be ported into the formal training path for a short local run.
- If a later formal replay diverges from these checks, do not train; inspect the training integration first.
- `v1.2 iter=15.pt` remains the conservative runtime checkpoint until v1.8 training beats it on targeted acceptance.
