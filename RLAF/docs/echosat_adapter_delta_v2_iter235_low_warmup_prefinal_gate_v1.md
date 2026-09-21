# EchoSAT Low-Warmup Pre-Final Gate Audit v1

This is an offline policy replay over corrected low-warmup CSVs. It does not train, does not rerun solver jobs, and does not use event-adapter final runtime to decide whether the adapter is allowed.

## Policy Inputs

- neutral weighted final CPU versus plain final CPU
- static weighted final CPU versus neutral weighted final CPU
- near-cap risk from plain, neutral weighted, or static weighted final CPU
- warmup event L2, event density, graph-gate-open evidence, and CNF scale

The family-aware policies are upper-bound audits, not deployable gates. The feature-only policy uses no family label and is included to check whether pre-final signals separate complete_coloring/php from random controls.

Important caveat: `docs/echosat_formula_equivalence_audit_v1.md` shows that the harder-baseline `complete_coloring/k9_color8` and `php_p9_h8` rows, and likewise `k10_color9` and `php_p10_h9`, share the same unordered CNF formula. Their DIMACS clause order differs. Therefore complete_coloring/php runtime differences in this audit are ordering/permutation diagnostics, not family-specific SAT symmetry evidence by themselves.

## Selected Thresholds

- weighted slowdown: abs>0.25, rel>0.1, logic=both
- near-cap veto fraction: 0.8
- event signal: L2>=50.0, density>=1.0, graph gate required=True
- feature-only scale window: 1 <= num_vars <= 120

## Artifacts

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_policy.csv`
- summary CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_summary.csv`
- by-family CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_by_family.csv`
- by-base CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_prefinal_gate_v1_by_base.csv`

## Overall

| policy_name | warmup_conflicts | rows | base_instances | adapter_allowed_fraction | policy_minus_plain_protocol_mean | policy_minus_plain_final_cpu_mean | adapter_minus_cached_final_cpu_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| always_event_adapter | 1 | 108 | 12 | 1 | -0.28918 | -0.427392 | 0.0357992 |
| family_complete_coloring_upper_bound | 1 | 108 | 12 | 0.231481 | -0.019044 | -0.0435195 | 0.0357992 |
| family_complete_php_upper_bound | 1 | 108 | 12 | 0.398148 | -0.0232014 | -0.067884 | 0.0357992 |
| feature_small_symmetric_prefinal_gate | 1 | 108 | 12 | 0.398148 | -0.0232014 | -0.067884 | 0.0357992 |
| weighted_hard_veto_only | 1 | 108 | 12 | 0.796296 | -0.178881 | -0.286523 | 0.0357992 |
| always_event_adapter | 3 | 108 | 12 | 1 | -0.237837 | -0.392833 | 0.0611377 |
| family_complete_coloring_upper_bound | 3 | 108 | 12 | 0.231481 | 0.0140374 | -0.01983 | 0.0611377 |
| family_complete_php_upper_bound | 3 | 108 | 12 | 0.398148 | 0.0612863 | 0.00556411 | 0.0611377 |
| feature_small_symmetric_prefinal_gate | 3 | 108 | 12 | 0.398148 | 0.0612863 | 0.00556411 | 0.0611377 |
| weighted_hard_veto_only | 3 | 108 | 12 | 0.787037 | -0.117096 | -0.237343 | 0.0611377 |
| always_event_adapter | 5 | 108 | 12 | 1 | -0.263085 | -0.419486 | 0.0460204 |
| family_complete_coloring_upper_bound | 5 | 108 | 12 | 0.222222 | 0.0120543 | -0.0207357 | 0.0460204 |
| family_complete_php_upper_bound | 5 | 108 | 12 | 0.388889 | 0.0514874 | -0.00161448 | 0.0460204 |
| feature_small_symmetric_prefinal_gate | 5 | 108 | 12 | 0.388889 | 0.0514874 | -0.00161448 | 0.0460204 |
| weighted_hard_veto_only | 5 | 108 | 12 | 0.787037 | -0.124734 | -0.245196 | 0.0460204 |
| always_event_adapter | 10 | 108 | 12 | 1 | -0.223724 | -0.376459 | 0.0850195 |
| family_complete_coloring_upper_bound | 10 | 108 | 12 | 0.231481 | 0.00926955 | -0.0211393 | 0.0850195 |
| family_complete_php_upper_bound | 10 | 108 | 12 | 0.398148 | 0.0224587 | -0.0291747 | 0.0850195 |
| feature_small_symmetric_prefinal_gate | 10 | 108 | 12 | 0.398148 | 0.0224587 | -0.0291747 | 0.0850195 |
| weighted_hard_veto_only | 10 | 108 | 12 | 0.787037 | -0.155032 | -0.271124 | 0.0850195 |
| always_event_adapter | 20 | 108 | 12 | 1 | -0.218856 | -0.366806 | 0.096246 |
| family_complete_coloring_upper_bound | 20 | 108 | 12 | 0.222222 | -0.000930833 | -0.0318887 | 0.096246 |
| family_complete_php_upper_bound | 20 | 108 | 12 | 0.388889 | 0.0441405 | -0.00651303 | 0.096246 |
| feature_small_symmetric_prefinal_gate | 20 | 108 | 12 | 0.388889 | 0.0441405 | -0.00651303 | 0.096246 |
| weighted_hard_veto_only | 20 | 108 | 12 | 0.787037 | -0.11104 | -0.225896 | 0.096246 |

## Feature-Only Gate By Family

| warmup_conflicts | family | base_instances | adapter_allowed_fraction | policy_minus_plain_protocol_mean | policy_minus_plain_final_cpu_mean | adapter_minus_cached_final_cpu_mean |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 3 | 0.925926 | -0.076176 | -0.174078 | -0.178184 |
| 1 | php | 2 | 1 | -0.0249445 | -0.146187 | -0.126658 |
| 1 | random_3sat_control | 7 | 0 | 0 | 0 | 0.173923 |
| 3 | complete_coloring | 3 | 0.925926 | 0.0561496 | -0.0793199 | -0.050511 |
| 3 | php | 2 | 1 | 0.283493 | 0.152365 | 0.162533 |
| 3 | random_3sat_control | 7 | 0 | 0 | 0 | 0.080017 |
| 5 | complete_coloring | 3 | 0.888889 | 0.048217 | -0.0829429 | -0.0661559 |
| 5 | php | 2 | 1 | 0.236599 | 0.114727 | 0.142758 |
| 5 | random_3sat_control | 7 | 0 | 0 | 0 | 0.0664568 |
| 10 | complete_coloring | 3 | 0.925926 | 0.0370782 | -0.0845573 | -0.0500174 |
| 10 | php | 2 | 1 | 0.0791346 | -0.048212 | -0.0324537 |
| 10 | random_3sat_control | 7 | 0 | 0 | 0 | 0.176456 |
| 20 | complete_coloring | 3 | 0.888889 | -0.00372333 | -0.127555 | -0.132304 |
| 20 | php | 2 | 1 | 0.270428 | 0.152254 | 0.159021 |
| 20 | random_3sat_control | 7 | 0 | 0 | 0 | 0.17626 |

## By Family

| policy_name | warmup_conflicts | family | base_instances | adapter_allowed_fraction | policy_minus_plain_protocol_mean | policy_minus_plain_final_cpu_mean | adapter_minus_cached_final_cpu_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| always_event_adapter | 1 | complete_coloring | 3 | 1 | -0.136405 | -0.242343 | -0.178184 |
| always_event_adapter | 1 | php | 2 | 1 | -0.0249445 | -0.146187 | -0.126658 |
| always_event_adapter | 1 | random_3sat_control | 7 | 1 | -0.430151 | -0.587043 | 0.173923 |
| family_complete_coloring_upper_bound | 1 | complete_coloring | 3 | 0.925926 | -0.076176 | -0.174078 | -0.178184 |
| family_complete_coloring_upper_bound | 1 | php | 2 | 0 | 0 | 0 | -0.126658 |
| family_complete_coloring_upper_bound | 1 | random_3sat_control | 7 | 0 | 0 | 0 | 0.173923 |
| family_complete_php_upper_bound | 1 | complete_coloring | 3 | 0.925926 | -0.076176 | -0.174078 | -0.178184 |
| family_complete_php_upper_bound | 1 | php | 2 | 1 | -0.0249445 | -0.146187 | -0.126658 |
| family_complete_php_upper_bound | 1 | random_3sat_control | 7 | 0 | 0 | 0 | 0.173923 |
| feature_small_symmetric_prefinal_gate | 1 | complete_coloring | 3 | 0.925926 | -0.076176 | -0.174078 | -0.178184 |
| feature_small_symmetric_prefinal_gate | 1 | php | 2 | 1 | -0.0249445 | -0.146187 | -0.126658 |
| feature_small_symmetric_prefinal_gate | 1 | random_3sat_control | 7 | 0 | 0 | 0 | 0.173923 |
| weighted_hard_veto_only | 1 | complete_coloring | 3 | 0.925926 | -0.076176 | -0.174078 | -0.178184 |
| weighted_hard_veto_only | 1 | php | 2 | 1 | -0.0249445 | -0.146187 | -0.126658 |
| weighted_hard_veto_only | 1 | random_3sat_control | 7 | 0.68254 | -0.266879 | -0.37481 | 0.173923 |
| always_event_adapter | 3 | complete_coloring | 3 | 1 | 0.0347414 | -0.111614 | -0.050511 |
| always_event_adapter | 3 | php | 2 | 1 | 0.283493 | 0.152365 | 0.162533 |
| always_event_adapter | 3 | random_3sat_control | 7 | 1 | -0.503608 | -0.669127 | 0.080017 |
| family_complete_coloring_upper_bound | 3 | complete_coloring | 3 | 0.925926 | 0.0561496 | -0.0793199 | -0.050511 |
| family_complete_coloring_upper_bound | 3 | php | 2 | 0 | 0 | 0 | 0.162533 |
| family_complete_coloring_upper_bound | 3 | random_3sat_control | 7 | 0 | 0 | 0 | 0.080017 |
| family_complete_php_upper_bound | 3 | complete_coloring | 3 | 0.925926 | 0.0561496 | -0.0793199 | -0.050511 |
| family_complete_php_upper_bound | 3 | php | 2 | 1 | 0.283493 | 0.152365 | 0.162533 |
| family_complete_php_upper_bound | 3 | random_3sat_control | 7 | 0 | 0 | 0 | 0.080017 |
| feature_small_symmetric_prefinal_gate | 3 | complete_coloring | 3 | 0.925926 | 0.0561496 | -0.0793199 | -0.050511 |
| feature_small_symmetric_prefinal_gate | 3 | php | 2 | 1 | 0.283493 | 0.152365 | 0.162533 |
| feature_small_symmetric_prefinal_gate | 3 | random_3sat_control | 7 | 0 | 0 | 0 | 0.080017 |
| weighted_hard_veto_only | 3 | complete_coloring | 3 | 0.925926 | 0.0561496 | -0.0793199 | -0.050511 |
| weighted_hard_veto_only | 3 | php | 2 | 1 | 0.283493 | 0.152365 | 0.162533 |
| weighted_hard_veto_only | 3 | random_3sat_control | 7 | 0.666667 | -0.305798 | -0.416411 | 0.080017 |
| always_event_adapter | 5 | complete_coloring | 3 | 1 | 0.0156995 | -0.132719 | -0.0661559 |
| always_event_adapter | 5 | php | 2 | 1 | 0.236599 | 0.114727 | 0.142758 |
| always_event_adapter | 5 | random_3sat_control | 7 | 1 | -0.525331 | -0.695018 | 0.0664568 |
| family_complete_coloring_upper_bound | 5 | complete_coloring | 3 | 0.888889 | 0.048217 | -0.0829429 | -0.0661559 |
| family_complete_coloring_upper_bound | 5 | php | 2 | 0 | 0 | 0 | 0.142758 |
| family_complete_coloring_upper_bound | 5 | random_3sat_control | 7 | 0 | 0 | 0 | 0.0664568 |
| family_complete_php_upper_bound | 5 | complete_coloring | 3 | 0.888889 | 0.048217 | -0.0829429 | -0.0661559 |
| family_complete_php_upper_bound | 5 | php | 2 | 1 | 0.236599 | 0.114727 | 0.142758 |
| family_complete_php_upper_bound | 5 | random_3sat_control | 7 | 0 | 0 | 0 | 0.0664568 |
| feature_small_symmetric_prefinal_gate | 5 | complete_coloring | 3 | 0.888889 | 0.048217 | -0.0829429 | -0.0661559 |
| feature_small_symmetric_prefinal_gate | 5 | php | 2 | 1 | 0.236599 | 0.114727 | 0.142758 |
| feature_small_symmetric_prefinal_gate | 5 | random_3sat_control | 7 | 0 | 0 | 0 | 0.0664568 |
| weighted_hard_veto_only | 5 | complete_coloring | 3 | 0.888889 | 0.048217 | -0.0829429 | -0.0661559 |
| weighted_hard_veto_only | 5 | php | 2 | 1 | 0.236599 | 0.114727 | 0.142758 |
| weighted_hard_veto_only | 5 | random_3sat_control | 7 | 0.68254 | -0.302094 | -0.417569 | 0.0664568 |
| always_event_adapter | 10 | complete_coloring | 3 | 1 | 0.0237699 | -0.109412 | -0.0500174 |
| always_event_adapter | 10 | php | 2 | 1 | 0.0791346 | -0.048212 | -0.0324537 |
| always_event_adapter | 10 | random_3sat_control | 7 | 1 | -0.416323 | -0.584692 | 0.176456 |
| family_complete_coloring_upper_bound | 10 | complete_coloring | 3 | 0.925926 | 0.0370782 | -0.0845573 | -0.0500174 |
| family_complete_coloring_upper_bound | 10 | php | 2 | 0 | 0 | 0 | -0.0324537 |
| family_complete_coloring_upper_bound | 10 | random_3sat_control | 7 | 0 | 0 | 0 | 0.176456 |
| family_complete_php_upper_bound | 10 | complete_coloring | 3 | 0.925926 | 0.0370782 | -0.0845573 | -0.0500174 |
| family_complete_php_upper_bound | 10 | php | 2 | 1 | 0.0791346 | -0.048212 | -0.0324537 |
| family_complete_php_upper_bound | 10 | random_3sat_control | 7 | 0 | 0 | 0 | 0.176456 |
| feature_small_symmetric_prefinal_gate | 10 | complete_coloring | 3 | 0.925926 | 0.0370782 | -0.0845573 | -0.0500174 |
| feature_small_symmetric_prefinal_gate | 10 | php | 2 | 1 | 0.0791346 | -0.048212 | -0.0324537 |
| feature_small_symmetric_prefinal_gate | 10 | random_3sat_control | 7 | 0 | 0 | 0 | 0.176456 |
| weighted_hard_veto_only | 10 | complete_coloring | 3 | 0.925926 | 0.0370782 | -0.0845573 | -0.0500174 |
| weighted_hard_veto_only | 10 | php | 2 | 1 | 0.0791346 | -0.048212 | -0.0324537 |
| weighted_hard_veto_only | 10 | random_3sat_control | 7 | 0.666667 | -0.304269 | -0.41477 | 0.176456 |
| always_event_adapter | 20 | complete_coloring | 3 | 1 | -0.0457717 | -0.18585 | -0.132304 |
| always_event_adapter | 20 | php | 2 | 1 | 0.270428 | 0.152254 | 0.159021 |
| always_event_adapter | 20 | random_3sat_control | 7 | 1 | -0.432831 | -0.592661 | 0.17626 |
| family_complete_coloring_upper_bound | 20 | complete_coloring | 3 | 0.888889 | -0.00372333 | -0.127555 | -0.132304 |
| family_complete_coloring_upper_bound | 20 | php | 2 | 0 | 0 | 0 | 0.159021 |
| family_complete_coloring_upper_bound | 20 | random_3sat_control | 7 | 0 | 0 | 0 | 0.17626 |
| family_complete_php_upper_bound | 20 | complete_coloring | 3 | 0.888889 | -0.00372333 | -0.127555 | -0.132304 |
| family_complete_php_upper_bound | 20 | php | 2 | 1 | 0.270428 | 0.152254 | 0.159021 |
| family_complete_php_upper_bound | 20 | random_3sat_control | 7 | 0 | 0 | 0 | 0.17626 |
| feature_small_symmetric_prefinal_gate | 20 | complete_coloring | 3 | 0.888889 | -0.00372333 | -0.127555 | -0.132304 |
| feature_small_symmetric_prefinal_gate | 20 | php | 2 | 1 | 0.270428 | 0.152254 | 0.159021 |
| feature_small_symmetric_prefinal_gate | 20 | random_3sat_control | 7 | 0 | 0 | 0 | 0.17626 |
| weighted_hard_veto_only | 20 | complete_coloring | 3 | 0.888889 | -0.00372333 | -0.127555 | -0.132304 |
| weighted_hard_veto_only | 20 | php | 2 | 1 | 0.270428 | 0.152254 | 0.159021 |
| weighted_hard_veto_only | 20 | random_3sat_control | 7 | 0.68254 | -0.266024 | -0.376085 | 0.17626 |

## Adapter-Allowed Base Rows

| policy_name | warmup_conflicts | family | base_instance_id | adapter_allowed_fraction | policy_minus_plain_protocol_mean | policy_minus_plain_final_cpu_mean | adapter_minus_cached_final_cpu_mean | event_l2_mean | event_density_mean | neutral_plain_delta_mean | static_neutral_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_event_adapter | 1 | complete_coloring | k10_color9 | 1 | -0.619592 | -0.725417 | -0.477147 | 136.913 | 1.52126 | -0.33681 | 0.08854 |
| always_event_adapter | 1 | complete_coloring | k8_color7 | 1 | 0.0955054 | -0.00685956 | -0.00795744 | 84.7712 | 1.51377 | 0.00358711 | -0.00248922 |
| always_event_adapter | 1 | complete_coloring | k9_color8 | 1 | 0.11487 | 0.00524722 | -0.049448 | 109.376 | 1.5191 | 0.0339392 | 0.020756 |
| always_event_adapter | 1 | php | php_p10_h9 | 1 | -0.114687 | -0.237284 | -0.215087 | 136.995 | 1.52217 | 0.00972889 | -0.0319267 |
| always_event_adapter | 1 | php | php_p9_h8 | 1 | 0.0647977 | -0.0550888 | -0.0382297 | 109.322 | 1.51836 | -0.0224967 | 0.00563756 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.135825 | -0.0148717 | 0.00450578 | 250.208 | 1.5638 | 0.0112008 | -0.0305782 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | 0.24144 | 0.0749746 | 0.526824 | 291.913 | 1.62174 | -0.359419 | -0.09243 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 1 | -0.381579 | -0.547321 | 0.00426356 | 331.934 | 1.50879 | -0.239954 | -0.31163 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.165103 | -0.0187044 | 0.183014 | 323.614 | 1.47097 | 0.0842977 | -0.286016 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | -3.44782 | -3.63262 | -0.191843 | 390.152 | 1.50059 | -2.06689 | -1.37389 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 1.37666 | 1.22287 | 0.667283 | 397.054 | 1.52713 | 0.713533 | -0.157949 |
| always_event_adapter | 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | -1.10069 | -1.19362 | 0.0234104 | 466.356 | 1.55452 | -0.0498367 | -1.1672 |
| family_complete_coloring_upper_bound | 1 | complete_coloring | k10_color9 | 0.777778 | -0.438904 | -0.520622 | -0.477147 | 136.913 | 1.52126 | -0.33681 | 0.08854 |
| family_complete_coloring_upper_bound | 1 | complete_coloring | k8_color7 | 1 | 0.0955054 | -0.00685956 | -0.00795744 | 84.7712 | 1.51377 | 0.00358711 | -0.00248922 |
| family_complete_coloring_upper_bound | 1 | complete_coloring | k9_color8 | 1 | 0.11487 | 0.00524722 | -0.049448 | 109.376 | 1.5191 | 0.0339392 | 0.020756 |
| family_complete_php_upper_bound | 1 | complete_coloring | k10_color9 | 0.777778 | -0.438904 | -0.520622 | -0.477147 | 136.913 | 1.52126 | -0.33681 | 0.08854 |
| family_complete_php_upper_bound | 1 | complete_coloring | k8_color7 | 1 | 0.0955054 | -0.00685956 | -0.00795744 | 84.7712 | 1.51377 | 0.00358711 | -0.00248922 |
| family_complete_php_upper_bound | 1 | complete_coloring | k9_color8 | 1 | 0.11487 | 0.00524722 | -0.049448 | 109.376 | 1.5191 | 0.0339392 | 0.020756 |
| family_complete_php_upper_bound | 1 | php | php_p10_h9 | 1 | -0.114687 | -0.237284 | -0.215087 | 136.995 | 1.52217 | 0.00972889 | -0.0319267 |
| family_complete_php_upper_bound | 1 | php | php_p9_h8 | 1 | 0.0647977 | -0.0550888 | -0.0382297 | 109.322 | 1.51836 | -0.0224967 | 0.00563756 |
| feature_small_symmetric_prefinal_gate | 1 | complete_coloring | k10_color9 | 0.777778 | -0.438904 | -0.520622 | -0.477147 | 136.913 | 1.52126 | -0.33681 | 0.08854 |
| feature_small_symmetric_prefinal_gate | 1 | complete_coloring | k8_color7 | 1 | 0.0955054 | -0.00685956 | -0.00795744 | 84.7712 | 1.51377 | 0.00358711 | -0.00248922 |
| feature_small_symmetric_prefinal_gate | 1 | complete_coloring | k9_color8 | 1 | 0.11487 | 0.00524722 | -0.049448 | 109.376 | 1.5191 | 0.0339392 | 0.020756 |
| feature_small_symmetric_prefinal_gate | 1 | php | php_p10_h9 | 1 | -0.114687 | -0.237284 | -0.215087 | 136.995 | 1.52217 | 0.00972889 | -0.0319267 |
| feature_small_symmetric_prefinal_gate | 1 | php | php_p9_h8 | 1 | 0.0647977 | -0.0550888 | -0.0382297 | 109.322 | 1.51836 | -0.0224967 | 0.00563756 |
| weighted_hard_veto_only | 1 | complete_coloring | k10_color9 | 0.777778 | -0.438904 | -0.520622 | -0.477147 | 136.913 | 1.52126 | -0.33681 | 0.08854 |
| weighted_hard_veto_only | 1 | complete_coloring | k8_color7 | 1 | 0.0955054 | -0.00685956 | -0.00795744 | 84.7712 | 1.51377 | 0.00358711 | -0.00248922 |
| weighted_hard_veto_only | 1 | complete_coloring | k9_color8 | 1 | 0.11487 | 0.00524722 | -0.049448 | 109.376 | 1.5191 | 0.0339392 | 0.020756 |
| weighted_hard_veto_only | 1 | php | php_p10_h9 | 1 | -0.114687 | -0.237284 | -0.215087 | 136.995 | 1.52217 | 0.00972889 | -0.0319267 |
| weighted_hard_veto_only | 1 | php | php_p9_h8 | 1 | 0.0647977 | -0.0550888 | -0.0382297 | 109.322 | 1.51836 | -0.0224967 | 0.00563756 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.135825 | -0.0148717 | 0.00450578 | 250.208 | 1.5638 | 0.0112008 | -0.0305782 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | 0.24144 | 0.0749746 | 0.526824 | 291.913 | 1.62174 | -0.359419 | -0.09243 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 0.666667 | -0.414116 | -0.523991 | 0.00426356 | 331.934 | 1.50879 | -0.239954 | -0.31163 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.165103 | -0.0187044 | 0.183014 | 323.614 | 1.47097 | 0.0842977 | -0.286016 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 0.333333 | -1.5504 | -1.61204 | -0.191843 | 390.152 | 1.50059 | -2.06689 | -1.37389 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 0.444444 | 0.33302 | 0.281377 | 0.667283 | 397.054 | 1.52713 | 0.713533 | -0.157949 |
| weighted_hard_veto_only | 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 0.333333 | -0.779023 | -0.810414 | 0.0234104 | 466.356 | 1.55452 | -0.0498367 | -1.1672 |
| always_event_adapter | 3 | complete_coloring | k10_color9 | 1 | -0.119447 | -0.270491 | -0.0244989 | 193.814 | 2.15349 | -0.338073 | 0.0920811 |
| always_event_adapter | 3 | complete_coloring | k8_color7 | 1 | 0.135413 | -0.00994789 | -0.0147982 | 124.872 | 2.22986 | 0.00300111 | 0.00184922 |
| always_event_adapter | 3 | complete_coloring | k9_color8 | 1 | 0.0882587 | -0.054403 | -0.112236 | 157.64 | 2.18944 | 0.0349644 | 0.0228686 |
| always_event_adapter | 3 | php | php_p10_h9 | 1 | 0.522536 | 0.390306 | 0.392858 | 193.511 | 2.15013 | 0.01101 | -0.0135622 |
| always_event_adapter | 3 | php | php_p9_h8 | 1 | 0.0444504 | -0.0855764 | -0.0677912 | 157.721 | 2.19056 | -0.018652 | 0.000866778 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.14237 | -0.0166778 | 0.00123389 | 361.807 | 2.26129 | 0.00583678 | -0.0237484 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.137628 | -0.309392 | 0.143616 | 431.033 | 2.39463 | -0.362872 | -0.0901373 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 1 | -0.376301 | -0.550217 | 0.00363956 | 456.134 | 2.07334 | -0.240295 | -0.313562 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.209344 | 0.0157676 | 0.209919 | 420.309 | 1.91049 | 0.0911084 | -0.28526 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | -4.02285 | -4.21611 | -0.794614 | 493.304 | 1.89732 | -2.08968 | -1.33182 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 1.73496 | 1.57201 | 0.972361 | 479.829 | 1.8455 | 0.743719 | -0.144073 |
| always_event_adapter | 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | -1.07515 | -1.17926 | 0.0239633 | 626.146 | 2.08715 | -0.0257418 | -1.17748 |
| family_complete_coloring_upper_bound | 3 | complete_coloring | k10_color9 | 0.777778 | -0.0552225 | -0.173609 | -0.0244989 | 193.814 | 2.15349 | -0.338073 | 0.0920811 |
| family_complete_coloring_upper_bound | 3 | complete_coloring | k8_color7 | 1 | 0.135413 | -0.00994789 | -0.0147982 | 124.872 | 2.22986 | 0.00300111 | 0.00184922 |
| family_complete_coloring_upper_bound | 3 | complete_coloring | k9_color8 | 1 | 0.0882587 | -0.054403 | -0.112236 | 157.64 | 2.18944 | 0.0349644 | 0.0228686 |
| family_complete_php_upper_bound | 3 | complete_coloring | k10_color9 | 0.777778 | -0.0552225 | -0.173609 | -0.0244989 | 193.814 | 2.15349 | -0.338073 | 0.0920811 |
| family_complete_php_upper_bound | 3 | complete_coloring | k8_color7 | 1 | 0.135413 | -0.00994789 | -0.0147982 | 124.872 | 2.22986 | 0.00300111 | 0.00184922 |
| family_complete_php_upper_bound | 3 | complete_coloring | k9_color8 | 1 | 0.0882587 | -0.054403 | -0.112236 | 157.64 | 2.18944 | 0.0349644 | 0.0228686 |
| family_complete_php_upper_bound | 3 | php | php_p10_h9 | 1 | 0.522536 | 0.390306 | 0.392858 | 193.511 | 2.15013 | 0.01101 | -0.0135622 |
| family_complete_php_upper_bound | 3 | php | php_p9_h8 | 1 | 0.0444504 | -0.0855764 | -0.0677912 | 157.721 | 2.19056 | -0.018652 | 0.000866778 |
| feature_small_symmetric_prefinal_gate | 3 | complete_coloring | k10_color9 | 0.777778 | -0.0552225 | -0.173609 | -0.0244989 | 193.814 | 2.15349 | -0.338073 | 0.0920811 |
| feature_small_symmetric_prefinal_gate | 3 | complete_coloring | k8_color7 | 1 | 0.135413 | -0.00994789 | -0.0147982 | 124.872 | 2.22986 | 0.00300111 | 0.00184922 |
| feature_small_symmetric_prefinal_gate | 3 | complete_coloring | k9_color8 | 1 | 0.0882587 | -0.054403 | -0.112236 | 157.64 | 2.18944 | 0.0349644 | 0.0228686 |
| feature_small_symmetric_prefinal_gate | 3 | php | php_p10_h9 | 1 | 0.522536 | 0.390306 | 0.392858 | 193.511 | 2.15013 | 0.01101 | -0.0135622 |
| feature_small_symmetric_prefinal_gate | 3 | php | php_p9_h8 | 1 | 0.0444504 | -0.0855764 | -0.0677912 | 157.721 | 2.19056 | -0.018652 | 0.000866778 |
| weighted_hard_veto_only | 3 | complete_coloring | k10_color9 | 0.777778 | -0.0552225 | -0.173609 | -0.0244989 | 193.814 | 2.15349 | -0.338073 | 0.0920811 |
| weighted_hard_veto_only | 3 | complete_coloring | k8_color7 | 1 | 0.135413 | -0.00994789 | -0.0147982 | 124.872 | 2.22986 | 0.00300111 | 0.00184922 |
| weighted_hard_veto_only | 3 | complete_coloring | k9_color8 | 1 | 0.0882587 | -0.054403 | -0.112236 | 157.64 | 2.18944 | 0.0349644 | 0.0228686 |
| weighted_hard_veto_only | 3 | php | php_p10_h9 | 1 | 0.522536 | 0.390306 | 0.392858 | 193.511 | 2.15013 | 0.01101 | -0.0135622 |
| weighted_hard_veto_only | 3 | php | php_p9_h8 | 1 | 0.0444504 | -0.0855764 | -0.0677912 | 157.721 | 2.19056 | -0.018652 | 0.000866778 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.14237 | -0.0166778 | 0.00123389 | 361.807 | 2.26129 | 0.00583678 | -0.0237484 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.137628 | -0.309392 | 0.143616 | 431.033 | 2.39463 | -0.362872 | -0.0901373 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 0.666667 | -0.41145 | -0.527606 | 0.00363956 | 456.134 | 2.07334 | -0.240295 | -0.313562 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 0.888889 | 0.174623 | 0.00539256 | 0.209919 | 420.309 | 1.91049 | 0.0911084 | -0.28526 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 0.333333 | -1.63672 | -1.70096 | -0.794614 | 493.304 | 1.89732 | -2.08968 | -1.33182 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 0.444444 | 0.494393 | 0.435554 | 0.972361 | 479.829 | 1.8455 | 0.743719 | -0.144073 |
| weighted_hard_veto_only | 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 0.333333 | -0.766175 | -0.801188 | 0.0239633 | 626.146 | 2.08715 | -0.0257418 | -1.17748 |
| always_event_adapter | 5 | complete_coloring | k10_color9 | 1 | -0.174824 | -0.329219 | -0.0680011 | 231.116 | 2.56796 | -0.364567 | 0.103349 |
| always_event_adapter | 5 | complete_coloring | k8_color7 | 1 | 0.139478 | -0.00949278 | -0.0148302 | 152.662 | 2.72611 | 0.00598478 | -0.000647333 |
| always_event_adapter | 5 | complete_coloring | k9_color8 | 1 | 0.0824445 | -0.0594448 | -0.115636 | 190.161 | 2.64112 | 0.0364289 | 0.0197627 |
| always_event_adapter | 5 | php | php_p10_h9 | 1 | 0.454031 | 0.330341 | 0.366203 | 230.262 | 2.55847 | -0.0193333 | -0.0165289 |
| always_event_adapter | 5 | php | php_p9_h8 | 1 | 0.0191659 | -0.100886 | -0.0806881 | 190.313 | 2.64324 | -0.0175953 | -0.00260278 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.140753 | -0.0158094 | 0.00355733 | 428.184 | 2.67615 | 0.00812933 | -0.0274961 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.165629 | -0.339408 | 0.110986 | 489.689 | 2.72049 | -0.360127 | -0.0902667 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 1 | -0.374365 | -0.550015 | 0.00723456 | 534.529 | 2.42968 | -0.242812 | -0.314437 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.235362 | 0.0359499 | 0.233249 | 474.341 | 2.1561 | 0.0863581 | -0.283657 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | -3.96338 | -4.16288 | -0.741857 | 551.022 | 2.11931 | -2.05736 | -1.36366 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 1.54231 | 1.37129 | 0.837428 | 540.515 | 2.07891 | 0.703007 | -0.169142 |
| always_event_adapter | 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | -1.09236 | -1.20426 | 0.0146001 | 725.716 | 2.41905 | -0.0469084 | -1.17195 |
| family_complete_coloring_upper_bound | 5 | complete_coloring | k10_color9 | 0.666667 | -0.0772715 | -0.179891 | -0.0680011 | 231.116 | 2.56796 | -0.364567 | 0.103349 |
| family_complete_coloring_upper_bound | 5 | complete_coloring | k8_color7 | 1 | 0.139478 | -0.00949278 | -0.0148302 | 152.662 | 2.72611 | 0.00598478 | -0.000647333 |
| family_complete_coloring_upper_bound | 5 | complete_coloring | k9_color8 | 1 | 0.0824445 | -0.0594448 | -0.115636 | 190.161 | 2.64112 | 0.0364289 | 0.0197627 |
| family_complete_php_upper_bound | 5 | complete_coloring | k10_color9 | 0.666667 | -0.0772715 | -0.179891 | -0.0680011 | 231.116 | 2.56796 | -0.364567 | 0.103349 |
| family_complete_php_upper_bound | 5 | complete_coloring | k8_color7 | 1 | 0.139478 | -0.00949278 | -0.0148302 | 152.662 | 2.72611 | 0.00598478 | -0.000647333 |
| family_complete_php_upper_bound | 5 | complete_coloring | k9_color8 | 1 | 0.0824445 | -0.0594448 | -0.115636 | 190.161 | 2.64112 | 0.0364289 | 0.0197627 |
| family_complete_php_upper_bound | 5 | php | php_p10_h9 | 1 | 0.454031 | 0.330341 | 0.366203 | 230.262 | 2.55847 | -0.0193333 | -0.0165289 |
| family_complete_php_upper_bound | 5 | php | php_p9_h8 | 1 | 0.0191659 | -0.100886 | -0.0806881 | 190.313 | 2.64324 | -0.0175953 | -0.00260278 |
| feature_small_symmetric_prefinal_gate | 5 | complete_coloring | k10_color9 | 0.666667 | -0.0772715 | -0.179891 | -0.0680011 | 231.116 | 2.56796 | -0.364567 | 0.103349 |
| feature_small_symmetric_prefinal_gate | 5 | complete_coloring | k8_color7 | 1 | 0.139478 | -0.00949278 | -0.0148302 | 152.662 | 2.72611 | 0.00598478 | -0.000647333 |
| feature_small_symmetric_prefinal_gate | 5 | complete_coloring | k9_color8 | 1 | 0.0824445 | -0.0594448 | -0.115636 | 190.161 | 2.64112 | 0.0364289 | 0.0197627 |
| feature_small_symmetric_prefinal_gate | 5 | php | php_p10_h9 | 1 | 0.454031 | 0.330341 | 0.366203 | 230.262 | 2.55847 | -0.0193333 | -0.0165289 |
| feature_small_symmetric_prefinal_gate | 5 | php | php_p9_h8 | 1 | 0.0191659 | -0.100886 | -0.0806881 | 190.313 | 2.64324 | -0.0175953 | -0.00260278 |
| weighted_hard_veto_only | 5 | complete_coloring | k10_color9 | 0.666667 | -0.0772715 | -0.179891 | -0.0680011 | 231.116 | 2.56796 | -0.364567 | 0.103349 |
| weighted_hard_veto_only | 5 | complete_coloring | k8_color7 | 1 | 0.139478 | -0.00949278 | -0.0148302 | 152.662 | 2.72611 | 0.00598478 | -0.000647333 |
| weighted_hard_veto_only | 5 | complete_coloring | k9_color8 | 1 | 0.0824445 | -0.0594448 | -0.115636 | 190.161 | 2.64112 | 0.0364289 | 0.0197627 |
| weighted_hard_veto_only | 5 | php | php_p10_h9 | 1 | 0.454031 | 0.330341 | 0.366203 | 230.262 | 2.55847 | -0.0193333 | -0.0165289 |
| weighted_hard_veto_only | 5 | php | php_p9_h8 | 1 | 0.0191659 | -0.100886 | -0.0806881 | 190.313 | 2.64324 | -0.0175953 | -0.00260278 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.140753 | -0.0158094 | 0.00355733 | 428.184 | 2.67615 | 0.00812933 | -0.0274961 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.165629 | -0.339408 | 0.110986 | 489.689 | 2.72049 | -0.360127 | -0.0902667 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 0.666667 | -0.409975 | -0.527443 | 0.00723456 | 534.529 | 2.42968 | -0.242812 | -0.314437 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.235362 | 0.0359499 | 0.233249 | 474.341 | 2.1561 | 0.0863581 | -0.283657 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 0.333333 | -1.59997 | -1.66608 | -0.741857 | 551.022 | 2.11931 | -2.05736 | -1.36366 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 0.444444 | 0.462317 | 0.403668 | 0.837428 | 540.515 | 2.07891 | 0.703007 | -0.169142 |
| weighted_hard_veto_only | 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 0.333333 | -0.777517 | -0.81386 | 0.0146001 | 725.716 | 2.41905 | -0.0469084 | -1.17195 |
| always_event_adapter | 10 | complete_coloring | k10_color9 | 1 | -0.105088 | -0.241653 | -0.000654444 | 315.107 | 3.50119 | -0.341719 | 0.10072 |
| always_event_adapter | 10 | complete_coloring | k8_color7 | 1 | 0.120334 | -0.0111617 | -0.0138484 | 218.567 | 3.90298 | 0.00329944 | -0.000612667 |
| always_event_adapter | 10 | complete_coloring | k9_color8 | 1 | 0.0560635 | -0.0754203 | -0.135549 | 265.018 | 3.68081 | 0.036874 | 0.023255 |
| always_event_adapter | 10 | php | php_p10_h9 | 1 | 0.153696 | 0.0256044 | 0.0404778 | 318.542 | 3.53935 | 0.00627778 | -0.0211511 |
| always_event_adapter | 10 | php | php_p9_h8 | 1 | 0.00457283 | -0.122028 | -0.105385 | 266.482 | 3.70114 | -0.0169227 | 0.000279444 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.144667 | -0.00866489 | 0.00647322 | 545.538 | 3.40961 | 0.0114029 | -0.026541 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.189214 | -0.352686 | 0.0965078 | 718.967 | 3.99426 | -0.356782 | -0.0924116 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 1 | -0.391214 | -0.557211 | 0.001954 | 534.529 | 2.42968 | -0.249733 | -0.309432 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.237729 | 0.0285917 | 0.223846 | 742.189 | 3.37359 | 0.088041 | -0.283295 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | -3.98645 | -4.19632 | -0.782787 | 717.447 | 2.75941 | -2.03319 | -1.38034 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 2.3723 | 2.19724 | 1.67745 | 782.528 | 3.00972 | 0.695334 | -0.175536 |
| always_event_adapter | 10 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | -1.10208 | -1.2038 | 0.0117532 | 913.152 | 3.04384 | -0.0428696 | -1.17268 |
| family_complete_coloring_upper_bound | 10 | complete_coloring | k10_color9 | 0.777778 | -0.0651627 | -0.16709 | -0.000654444 | 315.107 | 3.50119 | -0.341719 | 0.10072 |
| family_complete_coloring_upper_bound | 10 | complete_coloring | k8_color7 | 1 | 0.120334 | -0.0111617 | -0.0138484 | 218.567 | 3.90298 | 0.00329944 | -0.000612667 |
| family_complete_coloring_upper_bound | 10 | complete_coloring | k9_color8 | 1 | 0.0560635 | -0.0754203 | -0.135549 | 265.018 | 3.68081 | 0.036874 | 0.023255 |
| family_complete_php_upper_bound | 10 | complete_coloring | k10_color9 | 0.777778 | -0.0651627 | -0.16709 | -0.000654444 | 315.107 | 3.50119 | -0.341719 | 0.10072 |
| family_complete_php_upper_bound | 10 | complete_coloring | k8_color7 | 1 | 0.120334 | -0.0111617 | -0.0138484 | 218.567 | 3.90298 | 0.00329944 | -0.000612667 |
| family_complete_php_upper_bound | 10 | complete_coloring | k9_color8 | 1 | 0.0560635 | -0.0754203 | -0.135549 | 265.018 | 3.68081 | 0.036874 | 0.023255 |
| family_complete_php_upper_bound | 10 | php | php_p10_h9 | 1 | 0.153696 | 0.0256044 | 0.0404778 | 318.542 | 3.53935 | 0.00627778 | -0.0211511 |
| family_complete_php_upper_bound | 10 | php | php_p9_h8 | 1 | 0.00457283 | -0.122028 | -0.105385 | 266.482 | 3.70114 | -0.0169227 | 0.000279444 |
| feature_small_symmetric_prefinal_gate | 10 | complete_coloring | k10_color9 | 0.777778 | -0.0651627 | -0.16709 | -0.000654444 | 315.107 | 3.50119 | -0.341719 | 0.10072 |
| feature_small_symmetric_prefinal_gate | 10 | complete_coloring | k8_color7 | 1 | 0.120334 | -0.0111617 | -0.0138484 | 218.567 | 3.90298 | 0.00329944 | -0.000612667 |
| feature_small_symmetric_prefinal_gate | 10 | complete_coloring | k9_color8 | 1 | 0.0560635 | -0.0754203 | -0.135549 | 265.018 | 3.68081 | 0.036874 | 0.023255 |
| feature_small_symmetric_prefinal_gate | 10 | php | php_p10_h9 | 1 | 0.153696 | 0.0256044 | 0.0404778 | 318.542 | 3.53935 | 0.00627778 | -0.0211511 |
| feature_small_symmetric_prefinal_gate | 10 | php | php_p9_h8 | 1 | 0.00457283 | -0.122028 | -0.105385 | 266.482 | 3.70114 | -0.0169227 | 0.000279444 |
| weighted_hard_veto_only | 10 | complete_coloring | k10_color9 | 0.777778 | -0.0651627 | -0.16709 | -0.000654444 | 315.107 | 3.50119 | -0.341719 | 0.10072 |
| weighted_hard_veto_only | 10 | complete_coloring | k8_color7 | 1 | 0.120334 | -0.0111617 | -0.0138484 | 218.567 | 3.90298 | 0.00329944 | -0.000612667 |
| weighted_hard_veto_only | 10 | complete_coloring | k9_color8 | 1 | 0.0560635 | -0.0754203 | -0.135549 | 265.018 | 3.68081 | 0.036874 | 0.023255 |
| weighted_hard_veto_only | 10 | php | php_p10_h9 | 1 | 0.153696 | 0.0256044 | 0.0404778 | 318.542 | 3.53935 | 0.00627778 | -0.0211511 |
| weighted_hard_veto_only | 10 | php | php_p9_h8 | 1 | 0.00457283 | -0.122028 | -0.105385 | 266.482 | 3.70114 | -0.0169227 | 0.000279444 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.144667 | -0.00866489 | 0.00647322 | 545.538 | 3.40961 | 0.0114029 | -0.026541 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.189214 | -0.352686 | 0.0965078 | 718.967 | 3.99426 | -0.356782 | -0.0924116 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 0.666667 | -0.420855 | -0.531747 | 0.001954 | 534.529 | 2.42968 | -0.249733 | -0.309432 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.237729 | 0.0285917 | 0.223846 | 742.189 | 3.37359 | 0.088041 | -0.283295 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 0.333333 | -1.58371 | -1.65301 | -0.782787 | 717.447 | 2.75941 | -2.03319 | -1.38034 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 0.333333 | 0.463155 | 0.429863 | 1.67745 | 782.528 | 3.00972 | 0.695334 | -0.175536 |
| weighted_hard_veto_only | 10 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 0.333333 | -0.781654 | -0.815731 | 0.0117532 | 913.152 | 3.04384 | -0.0428696 | -1.17268 |
| always_event_adapter | 20 | complete_coloring | k10_color9 | 1 | -0.314767 | -0.460604 | -0.241731 | 464.298 | 5.15886 | -0.349013 | 0.13014 |
| always_event_adapter | 20 | complete_coloring | k8_color7 | 1 | 0.130297 | -0.00875133 | -0.0139912 | 327.142 | 5.84183 | 0.00594222 | -0.000702333 |
| always_event_adapter | 20 | complete_coloring | k9_color8 | 1 | 0.0471545 | -0.088193 | -0.14119 | 397.005 | 5.51396 | 0.0333616 | 0.0196353 |
| always_event_adapter | 20 | php | php_p10_h9 | 1 | 0.559196 | 0.43875 | 0.433783 | 465.379 | 5.17088 | -0.00415 | 0.00911667 |
| always_event_adapter | 20 | php | php_p9_h8 | 1 | -0.0183404 | -0.134242 | -0.115742 | 396.748 | 5.51038 | -0.023622 | 0.00512167 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 1 | 0.147447 | -0.00773856 | 0.00928344 | 896.408 | 5.60255 | 0.00843267 | -0.0254547 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 1 | -0.234269 | -0.410551 | 0.0390729 | 1132.64 | 6.29244 | -0.355875 | -0.0937493 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 1 | -0.371049 | -0.547587 | 0.00572633 | 534.529 | 2.42968 | -0.240196 | -0.313117 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 1 | 0.202172 | 0.0241262 | 0.227361 | 1216.96 | 5.53164 | 0.0835591 | -0.286793 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 1 | -4.0522 | -4.22914 | -0.745191 | 1081.89 | 4.16112 | -2.12065 | -1.36329 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 1 | 2.37797 | 2.22456 | 1.68529 | 1318.69 | 5.07187 | 0.692297 | -0.153023 |
| always_event_adapter | 20 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 1 | -1.09988 | -1.20231 | 0.0122793 | 1581.76 | 5.27252 | -0.0358652 | -1.17872 |

## Interpretation Rules

- `policy_minus_plain_protocol_mean < 0` is the end-to-end replay criterion against basic Glucose.
- `adapter_minus_cached_final_cpu_mean < 0` means the adapter changed final search beneficially after sharing the same cached-trace path.
- If only family-aware policies work, the current evidence is mechanism-local but not yet deployable.
- If feature-only policy excludes random controls but cannot separate formula-equivalent complete_coloring/php ordering cases, the next step is canonicalization/order-sensitivity analysis, not selector training.
- If feature-only policy admits random controls with large gains, the signal remains generic perturbation rather than SAT symmetry-specific.
