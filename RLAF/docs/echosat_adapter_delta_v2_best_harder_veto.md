# EchoSAT Weighted-Path Veto v0

This is a deployable-style rule audit: the veto inputs are plain/neutral/static calibration, near-cap risk, warmup overhead, and event signal. The rule does not use adapter final runtime as an input. It is still an offline replay over an existing runtime table.

## Artifacts

- policy CSV: `runs/analysis/echosat_adapter_delta_v2_best_harder_veto_policy.csv`
- sweep CSV: `runs/analysis/echosat_adapter_delta_v2_best_harder_veto_sweep.csv`

## Best Sweep Rows

| abs_threshold | rel_threshold | cap_veto | overhead_threshold | event_l2_epsilon | bases | weighted_vetoed_bases | event_vetoed_bases | policy_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_protocol_delta_mean | adapter_final_cpu_delta_mean | complete_coloring_bases | complete_coloring_event_vetoed_bases | complete_coloring_policy_protocol_delta_mean | complete_coloring_adapter_protocol_delta_mean | dominating_set_hex_bases | dominating_set_hex_event_vetoed_bases | dominating_set_hex_policy_protocol_delta_mean | dominating_set_hex_adapter_protocol_delta_mean | php_bases | php_event_vetoed_bases | php_policy_protocol_delta_mean | php_adapter_protocol_delta_mean | random_3sat_control_bases | random_3sat_control_event_vetoed_bases | random_3sat_control_policy_protocol_delta_mean | random_3sat_control_adapter_protocol_delta_mean | tseitin_complete_bases | tseitin_complete_event_vetoed_bases | tseitin_complete_policy_protocol_delta_mean | tseitin_complete_adapter_protocol_delta_mean | vertex_cover_torus_bases | vertex_cover_torus_event_vetoed_bases | vertex_cover_torus_policy_protocol_delta_mean | vertex_cover_torus_adapter_protocol_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | False | 0.25 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0 | False | 0.5 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0 | False | 1 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0 | False | 2 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0 | False | 5 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0.05 | False | 0.25 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0.05 | False | 0.5 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0.05 | False | 1 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0.05 | False | 2 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |
| 0 | 0.05 | False | 5 | 0 | 20 | 19 | 19 | -0.0161264 | -0.0172415 | 3.61495 | 1.69654 | 3 | 3 | 0 | 0.493301 | 4 | 4 | 0 | 9.33726 | 2 | 2 | 0 | 0.833146 | 7 | 6 | -0.0460754 | -0.199509 | 1 | 1 | 0 | 0.0829603 | 3 | 3 | 0 | 11.0391 |

## Family Summary For Selected Policy

| family | bases | weighted_vetoed_bases | event_vetoed_bases | policy_protocol_delta_mean | adapter_protocol_delta_mean | policy_final_cpu_delta_mean | adapter_final_cpu_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | 7 | 6 | 6 | -0.0460754 | -0.199509 | -0.0492614 | -0.688095 |
| complete_coloring | 3 | 3 | 3 | 0 | 0.493301 | 0 | -0.0980499 |
| dominating_set_hex | 4 | 4 | 4 | 0 | 9.33726 | 0 | 5.27571 |
| php | 2 | 1 | 2 | 0 | 0.833146 | 0 | -0.0387764 |
| tseitin_complete | 1 | 1 | 1 | 0 | 0.0829603 | 0 | 0.018907 |
| vertex_cover_torus | 3 | 3 | 3 | 0 | 11.0391 | 0 | 5.99914 |

## Interpretation

- `weighted_path_veto` uses neutral-vs-plain and static-vs-neutral slowdown plus optional near-cap risk.
- `event_path_veto` additionally includes warmup/event-overhead and weak-event-signal rules.
- This is a protocol variant candidate, not a learned selector and not a speedup claim.
