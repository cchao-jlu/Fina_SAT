# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.
The family summary separates valid rollout rows, event-positive rows,
zero-identity rows, and missing-event rows.

## Family Summary

| family | instances | orbits | mean_static_mu_range | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_event_l2_range | max_event_l2_range | mean_event_identity_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| php_exit_single | 18 | 54 | 1.973e-08 | 36 | 15 | 21 | 0 | 0.0833 | 0.3009 | 0.0833 |

## Event-Positive Summary

| family | instances | orbits | mean_static_mu_range | valid_rollout_rows | event_positive_rows | zero_identity_rows | missing_event_rows | mean_event_l2_range | max_event_l2_range | mean_event_identity_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| php_exit_single | 15 | 15 | 4.123e-08 | 15 | 15 | 0 | 0 | 0.2999 | 0.3009 | 0.2999 |

## Valid Row Filter

| family | event_row_valid_reason | rows |
| --- | --- | --- |
| php_exit_single | orbit_size_below_min | 18 |
| php_exit_single | valid | 36 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php_exit_single | php_exit_single_p5_h4 | base | SATISFIABLE | 0 | 1 | 0.00293 |
| php_exit_single | php_exit_single_p5_h4_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 1 | 0.003272 |
| php_exit_single | php_exit_single_p5_h4_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 1 | 0.003266 |
| php_exit_single | php_exit_single_p6_h5 | base | SATISFIABLE | 0 | 5 | 0.003204 |
| php_exit_single | php_exit_single_p6_h5_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 5 | 0.003313 |
| php_exit_single | php_exit_single_p6_h5_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 5 | 0.003308 |
| php_exit_single | php_exit_single_p7_h6 | base | SATISFIABLE | 0 | 6 | 0.003647 |
| php_exit_single | php_exit_single_p7_h6_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 6 | 0.003745 |
| php_exit_single | php_exit_single_p7_h6_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 6 | 0 |
| php_exit_single | php_exit_single_p8_h7 | base | SATISFIABLE | 0 | 7 | 0.001075 |
| php_exit_single | php_exit_single_p8_h7_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 7 | 0.004284 |
| php_exit_single | php_exit_single_p8_h7_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 7 | 0.001821 |
| php_exit_single | php_exit_single_p9_h8 | base | SATISFIABLE | 0 | 8 | 0.005353 |
| php_exit_single | php_exit_single_p9_h8_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 8 | 0.001734 |
| php_exit_single | php_exit_single_p9_h8_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 8 | 0.004901 |
| php_exit_single | php_exit_single_p10_h9 | base | SATISFIABLE | 0 | 9 | 0.005954 |
| php_exit_single | php_exit_single_p10_h9_perm1730 | perm_seed1730 | SATISFIABLE | 0 | 9 | 0.005925 |
| php_exit_single | php_exit_single_p10_h9_perm1731 | perm_seed1731 | SATISFIABLE | 0 | 9 | 0.002795 |
