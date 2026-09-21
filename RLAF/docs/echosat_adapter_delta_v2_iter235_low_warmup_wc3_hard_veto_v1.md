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

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc3_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc3_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.05 | 0.7 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.05 | 0.05 | 0.8 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.05 | 0.05 | 0.9 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.1 | 0.05 | 0.7 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.1 | 0.05 | 0.8 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.1 | 0.05 | 0.9 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.25 | 0.05 | 0.7 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.25 | 0.05 | 0.8 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.25 | 0.05 | 0.9 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |
| 0.5 | 0.05 | 0.7 | False | either | 12 | 11 | -0.011469 | -0.0257827 | -0.237837 | -0.392833 | 0.0611377 | 3 | 3 | 0 | 0.0347414 | -0.050511 | 2 | 2 | 0 | 0.283493 | 0.162533 | 7 | 6 | -0.0196611 | -0.503608 | 0.080017 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.0745571 | 0.0347414 | -0.0214503 | -0.111614 | -0.050511 |
| php | 2 | 0 | 0 | 0 | 0 | 0.283493 | 0.283493 | 0.152365 | 0.152365 | 0.162533 |
| random_3sat_control | 7 | 5 | 5 | 1 | 0 | 0.000677506 | -0.503608 | -0.0465815 | -0.669127 | 0.080017 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.338073 | 0.0920811 | 3.37678 | 3.03871 | 3.13079 | 0 | -0.119447 | -0.0244989 |
| complete_coloring | k8_color7 | False | False | False | False | 0.00300111 | 0.00184922 | 0.0406126 | 0.0436137 | 0.0454629 | 0.135413 | 0.135413 | -0.0147982 |
| complete_coloring | k9_color8 | False | False | False | False | 0.0349644 | 0.0228686 | 0.410817 | 0.445782 | 0.46865 | 0.0882587 | 0.0882587 | -0.112236 |
| php | php_p10_h9 | False | False | False | False | 0.01101 | -0.0135622 | 3.08164 | 3.09265 | 3.07909 | 0.522536 | 0.522536 | 0.392858 |
| php | php_p9_h8 | False | False | False | False | -0.018652 | 0.000866778 | 0.472456 | 0.453804 | 0.45467 | 0.0444504 | 0.0444504 | -0.0677912 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.00583678 | -0.0237484 | 0.058407 | 0.0642438 | 0.0404953 | 0.14237 | 0.14237 | 0.00123389 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.362872 | -0.0901373 | 0.463007 | 0.100135 | 0.00999789 | -0.137628 | -0.137628 | 0.143616 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.240295 | -0.313562 | 0.558537 | 0.318243 | 0.00468111 | 0 | -0.376301 | 0.00363956 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | True | True | False | False | 0.0911084 | -0.28526 | 0.561656 | 0.652764 | 0.367504 | 0 | 0.209344 | 0.209919 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -2.08968 | -1.33182 | 4.41149 | 2.32181 | 0.989988 | 0 | -4.02285 | -0.794614 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.743719 | -0.144073 | 4.25638 | 5.0001 | 4.85603 | 0 | 1.73496 | 0.972361 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0257418 | -1.17748 | 1.21362 | 1.18788 | 0.0103956 | 0 | -1.07515 | 0.0239633 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
