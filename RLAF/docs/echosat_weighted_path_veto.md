# EchoSAT Weighted-Path Veto v0

This is a deployable-style rule audit: the veto inputs are plain/neutral/static calibration, near-cap risk, warmup overhead, and event signal. The rule does not use adapter final runtime as an input. It is still an offline replay over an existing runtime table.

## Artifacts

- policy CSV: `runs/analysis/echosat_weighted_path_veto_policy.csv`
- sweep CSV: `runs/analysis/echosat_weighted_path_veto_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | cap_veto | overhead_threshold | event_l2_epsilon | bases | weighted_vetoed_bases | event_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_event_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | dominating_set_hex_bases | dominating_set_hex_event_vetoed_bases | dominating_set_hex_policy_protocol_delta_mean | dominating_set_hex_adapter_protocol_delta_mean | php_bases | php_event_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | random_3sat_control_bases | random_3sat_control_event_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | tseitin_complete_bases | tseitin_complete_event_vetoed_bases | tseitin_complete_policy_protocol_delta_mean | tseitin_complete_adapter_protocol_delta_mean | vertex_cover_torus_bases | vertex_cover_torus_event_vetoed_bases | vertex_cover_torus_policy_protocol_delta_mean | vertex_cover_torus_adapter_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | False | 0.25 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0 | False | 0.5 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0 | False | 1 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0 | False | 2 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0 | False | 5 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0.05 | False | 0.25 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0.05 | False | 0.5 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0.05 | False | 1 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0.05 | False | 2 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |
| 0 | 0.05 | False | 5 | 0 | 20 | 19 | 19 | -0.016121 | -0.0172013 | 3.6112 | 1.69118 | 3 | 3 | 0 | 0.465387 | 4 | 4 | 0 | 9.31651 | 2 | 2 | 0 | 0.834991 | 7 | 6 | -0.0460601 | -0.181831 | 1 | 1 | 0 | 0.0690585 | 3 | 3 | 0 | 11.0318 |

## Family Summary For Selected Policy

| family | bases | weighted_vetoed_bases | event_vetoed_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 7 | 6 | 6 | -0.0460601 | -0.181831 | -0.0491467 | -0.675143 |
| complete_coloring | 3 | 2 | 3 | 0 | 0.465387 | 0 | -0.130471 |
| dominating_set_hex | 4 | 4 | 4 | 0 | 9.31651 | 0 | 5.25632 |
| php | 2 | 1 | 2 | 0 | 0.834991 | 0 | -0.0313906 |
| tseitin_complete | 1 | 1 | 1 | 0 | 0.0690585 | 0 | 0.00152156 |
| vertex_cover_torus | 3 | 3 | 3 | 0 | 11.0318 | 0 | 5.99235 |

## Interpretation

- `weighted_path_veto` uses neutral-vs-plain and static-vs-neutral slowdown plus optional near-cap risk.
- `event_path_veto` additionally includes warmup/event-overhead and weak-event-signal rules.
- This is a protocol variant candidate, not a learned selector and not a speedup claim.
