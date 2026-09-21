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

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc20_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.1 | 0.7 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.1 | 0.8 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.1 | 0.9 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.25 | 0.7 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.25 | 0.8 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.25 | 0.9 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.1 | 0.1 | 0.7 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.1 | 0.1 | 0.8 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.1 | 0.1 | 0.9 | False | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |
| 0.05 | 0.1 | 0.7 | True | either | 12 | 10 | -0.0210508 | -0.0453994 | -0.218856 | -0.366806 | 0.096246 | 3 | 3 | 0 | -0.0457717 | -0.132304 | 2 | 1 | -0.00917021 | 0.270428 | 0.159021 | 7 | 6 | -0.0334671 | -0.432831 | 0.17626 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.0591505 | -0.0457717 | -0.0323148 | -0.18585 | -0.132304 |
| php | 2 | 0 | 0 | 0 | 0 | 0.270428 | 0.270428 | 0.152254 | 0.152254 | 0.159021 |
| random_3sat_control | 7 | 4 | 4 | 1 | 0 | 0.0164786 | -0.432831 | -0.0563091 | -0.592661 | 0.17626 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.349013 | 0.13014 | 3.37763 | 3.02861 | 3.15875 | 0 | -0.314767 | -0.241731 |
| complete_coloring | k8_color7 | False | False | False | False | 0.00594222 | -0.000702333 | 0.0392454 | 0.0451877 | 0.0444853 | 0.130297 | 0.130297 | -0.0139912 |
| complete_coloring | k9_color8 | False | False | False | False | 0.0333616 | 0.0196353 | 0.411329 | 0.44469 | 0.464326 | 0.0471545 | 0.0471545 | -0.14119 |
| php | php_p10_h9 | False | False | False | False | -0.00415 | 0.00911667 | 3.08877 | 3.08462 | 3.09373 | 0.559196 | 0.559196 | 0.433783 |
| php | php_p9_h8 | False | False | False | False | -0.023622 | 0.00512167 | 0.47069 | 0.447068 | 0.45219 | -0.0183404 | -0.0183404 | -0.115742 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.00843267 | -0.0254547 | 0.0559493 | 0.064382 | 0.0389273 | 0.147447 | 0.147447 | 0.00928344 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.355875 | -0.0937493 | 0.458928 | 0.103053 | 0.00930411 | -0.234269 | -0.234269 | 0.0390729 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.240196 | -0.313117 | 0.558652 | 0.318456 | 0.00533833 | 0 | -0.371049 | 0.00572633 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | False | False | False | False | 0.0835591 | -0.286793 | 0.566772 | 0.650331 | 0.363537 | 0.202172 | 0.202172 | 0.227361 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -2.12065 | -1.36329 | 4.46723 | 2.34657 | 0.983281 | 0 | -4.0522 | -0.745191 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.692297 | -0.153023 | 4.25511 | 4.94741 | 4.79438 | 0 | 2.37797 | 1.68529 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0358652 | -1.17872 | 1.22526 | 1.18939 | 0.0106692 | 0 | -1.09988 | 0.0122793 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
