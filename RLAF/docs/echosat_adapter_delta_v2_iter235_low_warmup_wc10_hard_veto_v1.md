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

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc10_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc10_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.05 | 0.7 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.05 | 0.05 | 0.8 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.05 | 0.05 | 0.9 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.05 | 0.1 | 0.7 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.05 | 0.1 | 0.8 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.05 | 0.1 | 0.9 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.1 | 0.05 | 0.7 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.1 | 0.05 | 0.8 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.1 | 0.05 | 0.9 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |
| 0.1 | 0.1 | 0.7 | False | either | 12 | 11 | -0.0157679 | -0.0293905 | -0.223724 | -0.376459 | 0.0850195 | 3 | 3 | 0 | 0.0237699 | -0.0500174 | 2 | 2 | 0 | 0.0791346 | -0.0324537 | 7 | 6 | -0.0270306 | -0.416323 | 0.176456 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.0587991 | 0.0237699 | -0.0288607 | -0.109412 | -0.0500174 |
| php | 2 | 0 | 0 | 0 | 0 | 0.0791346 | 0.0791346 | -0.048212 | -0.048212 | -0.0324537 |
| random_3sat_control | 7 | 4 | 4 | 1 | 0 | 0.0275974 | -0.416323 | -0.0475371 | -0.584692 | 0.176456 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.341719 | 0.10072 | 3.37919 | 3.03747 | 3.13819 | 0 | -0.105088 | -0.000654444 |
| complete_coloring | k8_color7 | False | False | False | False | 0.00329944 | -0.000612667 | 0.0404028 | 0.0437022 | 0.0430896 | 0.120334 | 0.120334 | -0.0138484 |
| complete_coloring | k9_color8 | False | False | False | False | 0.036874 | 0.023255 | 0.409286 | 0.44616 | 0.469415 | 0.0560635 | 0.0560635 | -0.135549 |
| php | php_p10_h9 | False | False | False | False | 0.00627778 | -0.0211511 | 3.09005 | 3.09633 | 3.07518 | 0.153696 | 0.153696 | 0.0404778 |
| php | php_p9_h8 | False | False | False | False | -0.0169227 | 0.000279444 | 0.469253 | 0.45233 | 0.452609 | 0.00457283 | 0.00457283 | -0.105385 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.0114029 | -0.026541 | 0.054021 | 0.0654239 | 0.0388829 | 0.144667 | 0.144667 | 0.00647322 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.356782 | -0.0924116 | 0.459255 | 0.102473 | 0.0100614 | -0.189214 | -0.189214 | 0.0965078 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.249733 | -0.309432 | 0.563564 | 0.313831 | 0.00439878 | 0 | -0.391214 | 0.001954 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | False | False | False | False | 0.088041 | -0.283295 | 0.560069 | 0.64811 | 0.364814 | 0.237729 | 0.237729 | 0.223846 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -2.03319 | -1.38034 | 4.39953 | 2.36633 | 0.98599 | 0 | -3.98645 | -0.782787 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.695334 | -0.175536 | 4.2907 | 4.98604 | 4.8105 | 0 | 2.3723 | 1.67745 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0428696 | -1.17268 | 1.22788 | 1.18501 | 0.0123353 | 0 | -1.10208 | 0.0117532 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
