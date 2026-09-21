# Adapter Negative-Case Audit

- source orbit CSV: `runs/analysis/symmetry_adapter_event_orbits.csv`

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
| no_activity_event_nonzero | 36 | 3 | 9 | 0.1909 | 1.026 | 0.03817 | 0.1924 | 36 |
| no_activity_zero_event | 3 | 1 | 3 | 0 | 0 | 3.179e-07 | 3.874e-07 | 0 |

## Family Breakdown

| negative_case_type | family | rows | instances | mean_event_l2 | max_event_l2 | mean_static_mu_range | mean_adapted_mu_range | max_adapted_mu_range | mean_adapter_minus_static_mu_range | violation_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | complete_coloring | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 0.192 | 0.1924 | 0.192 | 3 |
| no_activity_event_nonzero | dominating_set_hex | 30 | 3 | 0.03724 | 0.1033 | 1.428e-08 | 0.007407 | 0.01975 | 0.007407 | 30 |
| no_activity_event_nonzero | php | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 0.192 | 0.1924 | 0.192 | 3 |
| no_activity_zero_event | vertex_cover_torus | 3 | 3 | 0 | 0 | 3.353e-08 | 3.179e-07 | 3.874e-07 | 2.844e-07 | 0 |

## Largest Negative Adapter Ranges

| negative_case_type | family | instance_id | variant | orbit | orbit_size | event_feature_l2_range | static_mu_range | adapted_mu_range | adapter_negative_violation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | php | php_p4_h3_perm1731 | perm_seed1731 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 0.1924 | True |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1731 | perm_seed1731 | vertex_color_assignment | 12 | 1.026 | 2.235e-08 | 0.1924 | True |
| no_activity_event_nonzero | complete_coloring | k4_color3 | base | vertex_color_assignment | 12 | 1.026 | 7.451e-09 | 0.1924 | True |
| no_activity_event_nonzero | php | php_p4_h3_perm1730 | perm_seed1730 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 0.1924 | True |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1730 | perm_seed1730 | vertex_color_assignment | 12 | 0.8242 | 2.235e-08 | 0.1912 | True |
| no_activity_event_nonzero | php | php_p4_h3 | base | pigeon_hole_assignment | 12 | 0.8242 | 7.451e-09 | 0.1912 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o05_size2 | 2 | 0.0361 | 3.725e-09 | 0.01975 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o01_size2 | 2 | 0.0361 | 3.725e-08 | 0.01975 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o10_size2 | 2 | 0.1033 | 1.49e-08 | 0.01198 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o09_size2 | 2 | 0.1033 | 2.235e-08 | 0.01197 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o04_size2 | 2 | 0.08525 | 3.725e-09 | 0.01194 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o08_size2 | 2 | 0.08525 | 7.451e-09 | 0.01193 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o02_size2 | 2 | 0.06092 | 2.235e-08 | 0.0119 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o06_size2 | 2 | 0.06092 | 0 | 0.0119 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o01_size2 | 2 | 0.03023 | 3.725e-08 | 0.01186 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o01_size2 | 2 | 0.02179 | 2.608e-08 | 0.01185 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o03_size2 | 2 | 0.02179 | 7.451e-09 | 0.01185 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.49e-08 | 0.004001 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.49e-08 | 0.004001 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.863e-08 | 0.004001 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o09_size2 | 2 | 0.03568 | 0 | 0.003994 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o10_size2 | 2 | 0.03447 | 1.118e-08 | 0.003992 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o09_size2 | 2 | 0.03447 | 0 | 0.003991 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o10_size2 | 2 | 0.03314 | 7.451e-09 | 0.003989 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o04_size2 | 2 | 0.03015 | 3.725e-09 | 0.003982 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o04_size2 | 2 | 0.02846 | 2.98e-08 | 0.003979 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o08_size2 | 2 | 0.02846 | 0 | 0.003978 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o08_size2 | 2 | 0.02664 | 1.49e-08 | 0.003975 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o06_size2 | 2 | 0.02259 | 7.451e-09 | 0.003969 | True |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o06_size2 | 2 | 0.02035 | 3.725e-09 | 0.003966 | True |
