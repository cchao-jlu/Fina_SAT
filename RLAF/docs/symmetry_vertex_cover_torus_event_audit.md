# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.
The family summary separates valid rollout rows, event-positive rows,
zero-identity rows, and missing-event rows.

## Family Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 15 | 15 | 12 | 12 | 0 | 0 | 1.987e-08 | 3.542 | 5.07 | 3.542 | 5.07 |

## Event-Positive Summary

| family | instances | orbit_rows | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_static_mu_range_valid | mean_event_l2_valid | max_event_l2_valid | mean_event_l2_positive | max_event_l2_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | 12 | 12 | 12 | 12 | 0 | 0 | 1.987e-08 | 3.542 | 5.07 | 3.542 | 5.07 |

## Adapter Summary

_None._

## Valid Row Filter

| family | event_row_valid_reason | rows |
| --- | --- | --- |
| vertex_cover_torus | no_solver_activity | 3 |
| vertex_cover_torus | valid | 12 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event | base | UNSATISFIABLE | 5 | 4 | 0.02263 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 5 | 4 | 0.01217 |
| vertex_cover_torus | vertex_cover_torus_3x4_k4_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 5 | 4 | 0.01722 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event | base | UNSATISFIABLE | 7 | 6 | 0.01749 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 7 | 0.02354 |
| vertex_cover_torus | vertex_cover_torus_3x4_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 8 | 7 | 0.02844 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event | base | UNSATISFIABLE | 8 | 7 | 0.3443 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 7 | 6 | 0.3485 |
| vertex_cover_torus | vertex_cover_torus_3x5_k5_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 7 | 6 | 0.358 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event | base | UNSATISFIABLE | 12 | 12 | 0.6805 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1730 | perm_seed1730 | UNSATISFIABLE | 12 | 12 | 0.6393 |
| vertex_cover_torus | vertex_cover_torus_3x5_k6_event_perm1731 | perm_seed1731 | UNSATISFIABLE | 12 | 12 | 0.6425 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat | base | INDETERMINATE | 0 | 0 | 5.038 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | INDETERMINATE | 0 | 0 | 5.043 |
| vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | INDETERMINATE | 0 | 0 | 5.044 |
