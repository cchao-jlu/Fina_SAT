# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.

## Family Summary

| family | instances | orbits | mean_static_mu_range | mean_event_l2_range | max_event_l2_range | mean_event_identity_gain |
| --- | --- | --- | --- | --- | --- | --- |
| php | 2 | 2 | 1.118e-08 | 3.463 | 6.627 | 3.463 |

## Rollout Stats

| family | instance_id | variant | Result | conflicts | decisions | CPU time |
| --- | --- | --- | --- | --- | --- | --- |
| php | php_p4_h3 | base | UNSATISFIABLE | 0 | 0 | 0 |
| php | php_p5_h4 | base | INDETERMINATE | 20 | 28 | 0.003269 |
