# EchoSAT Weighted-Path Hard Veto v1

This audit replays a conservative hard-veto policy over an existing runtime table. It does not train a selector and does not use event-adapter final runtime as a veto input.

## Policy Inputs

- neutral weighted final CPU versus plain final CPU
- static weighted final CPU versus neutral weighted final CPU
- near-cap risk from plain, neutral weighted, or static weighted final CPU
- known expected-result mismatch risk, if present

Warmup/event overhead and weak event signal are deliberately not veto inputs in v1, so complete_coloring/php mechanism candidates are not rejected only because warmup is expensive.
The selected policy treats weighted slowdown as hard evidence only when both the absolute and relative slowdown thresholds are exceeded; this avoids vetoing tiny fast-instance fluctuations.

## Artifacts

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | dominating_set_hex_bases | dominating_set_hex_weighted_vetoed_bases | dominating_set_hex_policy_protocol_delta_mean | dominating_set_hex_adapter_protocol_delta_mean | dominating_set_hex_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean | tseitin_complete_bases | tseitin_complete_weighted_vetoed_bases | tseitin_complete_policy_protocol_delta_mean | tseitin_complete_adapter_protocol_delta_mean | tseitin_complete_adapter_cached_final_cpu_delta_mean | vertex_cover_torus_bases | vertex_cover_torus_weighted_vetoed_bases | vertex_cover_torus_policy_protocol_delta_mean | vertex_cover_torus_adapter_protocol_delta_mean | vertex_cover_torus_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.05 | 0.7 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.05 | 0.8 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.05 | 0.9 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.1 | 0.7 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.1 | 0.8 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.1 | 0.9 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.25 | 0.7 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.25 | 0.8 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.05 | 0.25 | 0.9 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |
| 0.1 | 0.05 | 0.7 | False | either | 20 | 18 | 0.00371161 | -0.0176302 | 3.60273 | 1.68532 | -0.0553018 | 3 | 3 | 0 | 0.419386 | -0.110496 | 4 | 4 | 0 | 9.32962 | 0.000161389 | 2 | 1 | 0.197952 | 0.74098 | -0.106058 | 7 | 6 | -0.0459531 | -0.167382 | -0.0797298 | 1 | 1 | 0 | 0.0686606 | -0.000390667 | 3 | 3 | 0 | 11.033 | -0.0015263 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.159463 | 0.419386 | 0.00472752 | -0.170023 | -0.110496 |
| dominating_set_hex | 4 | 4 | 4 | 0 | 3 | 0 | 9.32962 | 0 | 5.27041 | 0.000161389 |
| php | 2 | 0 | 0 | 0 | 0 | 0.74098 | 0.74098 | -0.136918 | -0.136918 | -0.106058 |
| random_3sat_control | 7 | 4 | 4 | 1 | 0 | -0.00570521 | -0.167382 | -0.0618487 | -0.653597 | -0.0797298 |
| tseitin_complete | 1 | 0 | 0 | 0 | 0 | 0.0686606 | 0.0686606 | 0.00330689 | 0.00330689 | -0.000390667 |
| vertex_cover_torus | 3 | 3 | 3 | 0 | 3 | 0 | 11.033 | 0 | 5.9935 | -0.0015263 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.319298 | 0.0967133 | 2.90407 | 2.58477 | 2.68149 | 0 | 0.779767 | -0.301668 |
| complete_coloring | k8_color7 | False | False | False | False | -0.000241556 | -0.00246822 | 0.0409059 | 0.0406643 | 0.0381961 | 0.039166 | 0.039166 | -0.00551211 |
| complete_coloring | k9_color8 | False | False | False | False | 0.032544 | 0.0141689 | 0.354558 | 0.387102 | 0.401271 | 0.439224 | 0.439224 | -0.0243084 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | True | True | False | False | 0.997556 | -0.0100667 | 0.132913 | 1.13047 | 1.1204 | 0 | 2.13137 | 0.00598667 |
| dominating_set_hex | dominating_set_hex_3x7_s5 | True | True | False | True | 4.71015 | 0.00387444 | 5.28696 | 9.99711 | 10.001 | 0 | 9.74918 | -0.00478667 |
| dominating_set_hex | dominating_set_hex_4x5_s5 | True | True | False | True | 7.63971 | -0.000771111 | 2.35742 | 9.99713 | 9.99636 | 0 | 12.6676 | -0.000652222 |
| dominating_set_hex | dominating_set_hex_5x4_s5 | True | True | False | True | 7.74129 | -0.000754444 | 2.25629 | 9.99758 | 9.99683 | 0 | 12.7703 | 9.77778e-05 |
| php | php_p10_h9 | False | False | False | False | -0.0269556 | -0.0117933 | 2.66165 | 2.63469 | 2.6229 | 1.08606 | 1.08606 | -0.224721 |
| php | php_p9_h8 | False | False | False | False | -0.0223417 | -0.000629889 | 0.409532 | 0.387191 | 0.386561 | 0.395904 | 0.395904 | 0.0126056 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.00498178 | -0.018165 | 0.0484919 | 0.0534737 | 0.0353087 | 0.0416015 | 0.0416015 | 0.00704756 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.285523 | -0.0743206 | 0.36908 | 0.083557 | 0.00923644 | -0.321672 | -0.321672 | 0.0176058 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.200817 | -0.248576 | 0.453496 | 0.252679 | 0.00410233 | 0 | -0.427115 | 0.00427244 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | False | False | False | False | 0.073298 | -0.22244 | 0.447979 | 0.521277 | 0.298837 | 0.240134 | 0.240134 | 0.0645741 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -1.64605 | -1.05103 | 3.51105 | 1.86499 | 0.813965 | 0 | -2.61142 | -0.768928 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.569253 | 0.0326489 | 3.38482 | 3.95407 | 3.98672 | 0 | 2.83322 | 0.114893 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0148459 | -0.93548 | 0.959903 | 0.945057 | 0.00957756 | 0 | -0.926414 | 0.00242622 |
| tseitin_complete | tseitin_k7_odd | False | False | False | False | 0.00605089 | -0.00235333 | 0.0494541 | 0.055505 | 0.0531517 | 0.0686606 | 0.0686606 | -0.000390667 |
| vertex_cover_torus | vertex_cover_torus_3x6_k6_event | True | True | False | True | 8.60628 | 0.00123556 | 1.38979 | 9.99607 | 9.99731 | 0 | 13.6318 | -0.00104333 |
| vertex_cover_torus | vertex_cover_torus_3x6_k7_event | True | True | False | True | 6.92878 | -0.000351111 | 3.0705 | 9.99928 | 9.99893 | 0 | 11.9604 | -0.00226889 |
| vertex_cover_torus | vertex_cover_torus_4x5_k6_event | True | True | False | True | 2.44792 | 0.00120111 | 7.54781 | 9.99573 | 9.99693 | 0 | 7.50683 | -0.00126667 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
