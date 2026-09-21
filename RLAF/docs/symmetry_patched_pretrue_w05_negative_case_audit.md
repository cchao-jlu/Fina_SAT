# Adapter Negative-Case Audit

- source orbit CSV: `runs/analysis/symmetry_patched_pretrue_w05_event_orbits.csv`

This audit checks whether the event adapter creates output separation
on negative cases where it should ideally stay close to static output:
valid zero-identity rows, no-solver-activity rows, and missing-events
rows. It is a representation guardrail, not a solver speedup claim.

`no_activity_event_nonzero` is separated from `no_activity_zero_event`
because enhanced event features can contain propagation/assignment
signals even when decisions and conflicts are zero.

## Overall

| negative_case_type | rows | families | instances | mean_event_l2 | max_event_l2 | mean_adapted_mu_range | max_adapted_mu_range | violation_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | 6 | 2 | 6 | 0.959 | 1.026 | 1.738e-08 | 2.235e-08 | 0 |

## Family Breakdown

| negative_case_type | family | rows | instances | mean_event_l2 | max_event_l2 | mean_static_mu_range | mean_adapted_mu_range | max_adapted_mu_range | mean_adapter_minus_static_mu_range | violation_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | complete_coloring | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 1.738e-08 | 2.235e-08 | 0 | 0 |
| no_activity_event_nonzero | php | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 1.738e-08 | 2.235e-08 | 0 | 0 |

## Largest Negative Adapter Ranges

| negative_case_type | family | instance_id | variant | orbit | orbit_size | event_feature_l2_range | static_mu_range | adapted_mu_range | adapter_negative_violation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | php | php_p4_h3_perm1730 | perm_seed1730 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | php | php_p4_h3_perm1731 | perm_seed1731 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1731 | perm_seed1731 | vertex_color_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1730 | perm_seed1730 | vertex_color_assignment | 12 | 0.8242 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | php | php_p4_h3 | base | pigeon_hole_assignment | 12 | 0.8242 | 7.451e-09 | 7.451e-09 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3 | base | vertex_color_assignment | 12 | 1.026 | 7.451e-09 | 7.451e-09 | False |
