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

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc1_hard_veto_v1_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_wc1_hard_veto_v1_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | near_cap_fraction | cap_veto | slowdown_logic | bases | weighted_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_weighted_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | complete_coloring_adapter_cached_final_cpu_delta_mean | php_bases | php_weighted_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | php_adapter_cached_final_cpu_delta_mean | random_3sat_control_bases | random_3sat_control_weighted_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | random_3sat_control_adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.25 | 0.7 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 0.5 | 0.25 | 0.8 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 0.5 | 0.25 | 0.9 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 1 | 0.25 | 0.7 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 1 | 0.25 | 0.8 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 1 | 0.25 | 0.9 | False | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 0.5 | 0.25 | 0.7 | True | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 0.5 | 0.25 | 0.8 | True | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 0.5 | 0.25 | 0.9 | True | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |
| 1 | 0.25 | 0.7 | True | either | 12 | 7 | -0.0260975 | -0.0781307 | -0.28918 | -0.427392 | 0.0357992 | 3 | 1 | -0.168241 | -0.136405 | -0.178184 | 2 | 0 | -0.0249445 | -0.0249445 | -0.126658 | 7 | 6 | 0.0344915 | -0.430151 | 0.173923 |

## Selected Policy By Family

| family | bases | weighted_vetoed_bases | neutral_risk_bases | static_risk_bases | cap_risk_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean | adapter_cached_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | 3 | 1 | 0 | 1 | 0 | 0.0701253 | -0.136405 | -0.000537444 | -0.242343 | -0.178184 |
| php | 2 | 0 | 0 | 0 | 0 | -0.0249445 | -0.0249445 | -0.146187 | -0.146187 | -0.126658 |
| random_3sat_control | 7 | 4 | 4 | 1 | 0 | 0.0774811 | -0.430151 | 0.00591406 | -0.587043 | 0.173923 |

## Selected Policy By Base

| family | base_instance_id | weighted_path_veto | neutral_slowdown_risk | static_slowdown_risk | cap_risk | neutral_delta_cpu_mean | static_delta_vs_neutral_cpu_mean | plain_final_cpu_mean | neutral_final_cpu_mean | static_final_cpu_mean | policy_minus_plain_protocol | adapter_minus_plain_protocol | adapter_minus_cached_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | True | False | True | False | -0.33681 | 0.08854 | 3.37694 | 3.04013 | 3.12867 | 0 | -0.619592 | -0.477147 |
| complete_coloring | k8_color7 | False | False | False | False | 0.00358711 | -0.00248922 | 0.0422787 | 0.0458658 | 0.0433766 | 0.0955054 | 0.0955054 | -0.00795744 |
| complete_coloring | k9_color8 | False | False | False | False | 0.0339392 | 0.020756 | 0.414686 | 0.448625 | 0.469381 | 0.11487 | 0.11487 | -0.049448 |
| php | php_p10_h9 | False | False | False | False | 0.00972889 | -0.0319267 | 3.09788 | 3.10761 | 3.07568 | -0.114687 | -0.114687 | -0.215087 |
| php | php_p9_h8 | False | False | False | False | -0.0224967 | 0.00563756 | 0.469461 | 0.446964 | 0.452601 | 0.0647977 | 0.0647977 | -0.0382297 |
| random_3sat_control | random_3sat_control_v160_c704_seed2615 | False | False | False | False | 0.0112008 | -0.0305782 | 0.0561904 | 0.0673912 | 0.036813 | 0.135825 | 0.135825 | 0.00450578 |
| random_3sat_control | random_3sat_control_v180_c760_seed3301 | False | False | False | False | -0.359419 | -0.09243 | 0.460758 | 0.101338 | 0.00890844 | 0.24144 | 0.24144 | 0.526824 |
| random_3sat_control | random_3sat_control_v220_c928_seed3303 | True | True | False | False | -0.239954 | -0.31163 | 0.557897 | 0.317943 | 0.00631222 | 0 | -0.381579 | 0.00426356 |
| random_3sat_control | random_3sat_control_v220_c942_seed3304 | False | False | False | False | 0.0842977 | -0.286016 | 0.568424 | 0.652722 | 0.366706 | 0.165103 | 0.165103 | 0.183014 |
| random_3sat_control | random_3sat_control_v260_c1097_seed3305 | True | True | True | False | -2.06689 | -1.37389 | 4.4266 | 2.3597 | 0.985817 | 0 | -3.44782 | -0.191843 |
| random_3sat_control | random_3sat_control_v260_c1113_seed3306 | True | True | False | False | 0.713533 | -0.157949 | 4.25967 | 4.97321 | 4.81526 | 0 | 1.37666 | 0.667283 |
| random_3sat_control | random_3sat_control_v300_c1266_seed3307 | True | True | False | False | -0.0498367 | -1.1672 | 1.22729 | 1.17745 | 0.010254 | 0 | -1.10069 | 0.0234104 |

## Interpretation

- This veto is intended to isolate weighted-path risk, not to solve event overhead.
- A good policy should avoid hex/torus near-cap or weighted-path failures without vetoing all complete_coloring/php candidates.
- Any later deployable gate still must use only pre-final information; this offline replay is not a speedup claim.
