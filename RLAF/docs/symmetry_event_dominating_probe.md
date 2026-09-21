# Event Symmetry Audit

- checkpoint: `/home/sunshixin/chenchao/my_rlaf/runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`

This audit is a representation test, not a solver-performance claim.
It measures whether short solver rollouts create within-orbit event
identity. Adapter output separation is reported only when the
checkpoint actually contains an event adapter.

## Family Summary

| family | instances | orbits | mean_static_mu_range | ok_orbit_rows | missing_event_rows |
| --- | --- | --- | --- | --- | --- |
| dominating_set_hex | 1 | 1 | 0.0002246 | 0 | 1 |

## Rollout Stats

| family | instance_id | variant |
| --- | --- | --- |
| dominating_set_hex | dominating_set_hex_4x7_s7 | base |
