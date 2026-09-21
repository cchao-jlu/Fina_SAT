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

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc5_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc5_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.05 | 0.7 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.05 | 0.05 | 0.8 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.05 | 0.05 | 0.9 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.05 | 0.1 | 0.7 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.05 | 0.1 | 0.8 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.05 | 0.1 | 0.9 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.1 | 0.05 | 0.7 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.1 | 0.05 | 0.8 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.1 | 0.05 | 0.9 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |
| 0.1 | 0.1 | 0.7 | False | either | 12 | 11 | -0.0138024 | -0.028284 | -0.263085 | -0.419486 | 0.0460204 | 3 | 3 | 0 | 0.0156995 | -0.0661559 | 2 | 2 | 0 | 0.236599 | 0.142758 | 7 | 6 | -0.0236613 | -0.525331 | 0.0664568 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.0739742 | 0.0156995 | -0.0229792 | -0.132719 | -0.0661559 |
| php | 2 | 0 | 0 | 0 | 0 | 0.236599 | 0.236599 | 0.114727 | 0.114727 | 0.142758 |
| random_3sat_control | 7 | 4 | 4 | 1 | 0 | 0.0300694 | -0.525331 | -0.0456096 | -0.695018 | 0.0664568 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.364567 | 0.103349 | 3.39686 | 3.03229 | 3.13564 | 0 | -0.174824 | -0.0680011 |
| complete_coloring | k8_color7 | False | False | False | False | 0.00598478 | -0.000647333 | 0.0385382 | 0.044523 | 0.0438757 | 0.139478 | 0.139478 | -0.0148302 |
| complete_coloring | k9_color8 | False | False | False | False | 0.0364289 | 0.0197627 | 0.411375 | 0.447804 | 0.467567 | 0.0824445 | 0.0824445 | -0.115636 |
| php | php_p10_h9 | False | False | False | False | -0.0193333 | -0.0165289 | 3.10362 | 3.08429 | 3.06776 | 0.454031 | 0.454031 | 0.366203 |
| php | php_p9_h8 | False | False | False | False | -0.0175953 | -0.00260278 | 0.470257 | 0.452662 | 0.450059 | 0.0191659 | 0.0191659 | -0.0806881 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.00812933 | -0.0274961 | 0.057417 | 0.0655463 | 0.0380502 | 0.140753 | 0.140753 | 0.00355733 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.360127 | -0.0902667 | 0.46007 | 0.0999424 | 0.00967578 | -0.165629 | -0.165629 | 0.110986 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.242812 | -0.314437 | 0.561358 | 0.318547 | 0.00410933 | 0 | -0.374365 | 0.00723456 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | False | False | False | False | 0.0863581 | -0.283657 | 0.560585 | 0.646943 | 0.363286 | 0.235362 | 0.235362 | 0.233249 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -2.05736 | -1.36366 | 4.407 | 2.34964 | 0.985979 | 0 | -3.96338 | -0.741857 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.703007 | -0.169142 | 4.2834 | 4.98641 | 4.81727 | 0 | 1.54231 | 0.837428 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0469084 | -1.17195 | 1.22947 | 1.18256 | 0.0106151 | 0 | -1.09236 | 0.0146001 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
