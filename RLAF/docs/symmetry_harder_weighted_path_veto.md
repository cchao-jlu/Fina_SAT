# Weighted-Path Veto Offline Audit

This evaluates rule-based veto policies on the already measured harder-baseline runtime table. It does not rerun solvers and does not train a selector.

## Artifacts

- policy CSV: `runs/analysis/symmetry_harder_weighted_path_veto_policy.csv`
- sweep CSV: `runs/analysis/symmetry_harder_weighted_path_veto_sweep.csv`

## Best Sweep Rows

| slowdown_threshold | cap_veto | bases | vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | policy_improves_vs_plain_protocol_bases | policy_improves_vs_plain_final_cpu_bases | policy_improves_vs_adapter_protocol_bases | policy_improves_vs_adapter_final_cpu_bases | complete_coloring_bases | complete_coloring_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | dominating_set_hex_bases | dominating_set_hex_vetoed_bases | dominating_set_hex_policy_protocol_delta_mean | dominating_set_hex_adapter_protocol_delta_mean | php_bases | php_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | random_3sat_control_bases | random_3sat_control_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | tseitin_complete_bases | tseitin_complete_vetoed_bases | tseitin_complete_policy_protocol_delta_mean | tseitin_complete_adapter_protocol_delta_mean | vertex_cover_torus_bases | vertex_cover_torus_vetoed_bases | vertex_cover_torus_policy_protocol_delta_mean | vertex_cover_torus_adapter_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | False | 20 | 14 | -0.142206 | -0.276785 | 3.6112 | 1.69118 | 4 | 5 | 14 | 9 | 3 | 2 | 0.326106 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 1 | 0.210989 | 0.834991 | 7 | 3 | -0.606344 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | True | 20 | 14 | -0.142206 | -0.276785 | 3.6112 | 1.69118 | 4 | 5 | 14 | 9 | 3 | 2 | 0.326106 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 1 | 0.210989 | 0.834991 | 7 | 3 | -0.606344 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.01 | False | 20 | 11 | -0.134638 | -0.277547 | 3.6112 | 1.69118 | 4 | 7 | 11 | 8 | 3 | 1 | 0.341755 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 1 | 0.210989 | 0.834991 | 7 | 2 | -0.601294 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.01 | True | 20 | 11 | -0.134638 | -0.277547 | 3.6112 | 1.69118 | 4 | 7 | 11 | 8 | 3 | 1 | 0.341755 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 1 | 0.210989 | 0.834991 | 7 | 2 | -0.601294 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.05 | False | 20 | 9 | -0.0536929 | -0.283348 | 3.6112 | 1.69118 | 4 | 9 | 9 | 8 | 3 | 0 | 0.465387 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 0 | 0.834991 | 0.834991 | 7 | 2 | -0.601294 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.05 | True | 20 | 9 | -0.0536929 | -0.283348 | 3.6112 | 1.69118 | 4 | 9 | 9 | 8 | 3 | 0 | 0.465387 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 0 | 0.834991 | 0.834991 | 7 | 2 | -0.601294 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.1 | False | 20 | 8 | -0.0380343 | -0.284164 | 3.6112 | 1.69118 | 4 | 10 | 8 | 8 | 3 | 0 | 0.465387 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 0 | 0.834991 | 0.834991 | 7 | 1 | -0.556555 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0.5 | False | 20 | 8 | -0.0380343 | -0.284164 | 3.6112 | 1.69118 | 4 | 10 | 8 | 8 | 3 | 0 | 0.465387 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 0 | 0.834991 | 0.834991 | 7 | 1 | -0.556555 | -0.181831 | 1 | 0 | 0.0690585 | 0.0690585 | 3 | 3 | 0 | 11.0318 |

## Family Summary For Selected Policy

| family | bases | vetoed_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 7 | 2 | -0.601294 | -0.181831 | -0.744898 | -0.675143 |
| dominating_set_hex | 4 | 4 | 0 | 9.31651 | 0 | 5.25632 |
| vertex_cover_torus | 3 | 3 | 0 | 11.0318 | 0 | 5.99235 |
| tseitin_complete | 1 | 0 | 0.0690585 | 0.0690585 | 0.00152156 | 0.00152156 |
| complete_coloring | 3 | 0 | 0.465387 | 0.465387 | -0.130471 | -0.130471 |
| php | 2 | 0 | 0.834991 | 0.834991 | -0.0313906 | -0.0313906 |

## Interpretation

- A vetoed base uses plain Glucose instead of the event-adapter weighted path.
- The rule uses already observed neutral/static weighted slowdown and optional near-cap risk, so this is an oracle-style diagnostic, not a deployable gate.
- If veto sharply improves hex/torus without killing random-control wins, weighted-path risk is a real blocker and should be handled before training a selector.
