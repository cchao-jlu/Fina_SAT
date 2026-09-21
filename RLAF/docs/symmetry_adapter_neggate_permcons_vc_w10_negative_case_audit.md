# Adapter Negative-Case Audit

- source orbit CSV: `runs/analysis/symmetry_adapter_neggate_permcons_vc_w10_event_orbits.csv`

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
| no_activity_event_nonzero | 36 | 3 | 9 | 0.1909 | 1.026 | 1.48e-08 | 3.725e-08 | 0 |
| no_activity_zero_event | 3 | 1 | 3 | 0 | 0 | 3.353e-08 | 4.843e-08 | 0 |

## Family Breakdown

| negative_case_type | family | rows | instances | mean_event_l2 | max_event_l2 | mean_static_mu_range | mean_adapted_mu_range | max_adapted_mu_range | mean_adapter_minus_static_mu_range | violation_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_event_nonzero | complete_coloring | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 1.738e-08 | 2.235e-08 | 0 | 0 |
| no_activity_event_nonzero | dominating_set_hex | 30 | 3 | 0.03724 | 0.1033 | 1.428e-08 | 1.428e-08 | 3.725e-08 | 0 | 0 |
| no_activity_event_nonzero | php | 3 | 3 | 0.959 | 1.026 | 1.738e-08 | 1.738e-08 | 2.235e-08 | 0 | 0 |
| no_activity_zero_event | vertex_cover_torus | 3 | 3 | 0 | 0 | 3.353e-08 | 3.353e-08 | 4.843e-08 | 0 | 0 |

## Largest Negative Adapter Ranges

| negative_case_type | family | instance_id | variant | orbit | orbit_size | event_feature_l2_range | static_mu_range | adapted_mu_range | adapter_negative_violation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_activity_zero_event | vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1731 | perm_seed1731 | torus_vertex | 20 | 0 | 4.843e-08 | 4.843e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o01_size2 | 2 | 0.03023 | 3.725e-08 | 3.725e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o01_size2 | 2 | 0.0361 | 3.725e-08 | 3.725e-08 | False |
| no_activity_zero_event | vertex_cover_torus | vertex_cover_torus_4x5_norat | base | torus_vertex | 20 | 0 | 3.353e-08 | 3.353e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o04_size2 | 2 | 0.02846 | 2.98e-08 | 2.98e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o05_size2 | 2 | 0.007285 | 2.608e-08 | 2.608e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o01_size2 | 2 | 0.02179 | 2.608e-08 | 2.608e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o02_size2 | 2 | 0.01798 | 2.608e-08 | 2.608e-08 | False |
| no_activity_event_nonzero | php | php_p4_h3_perm1731 | perm_seed1731 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | php | php_p4_h3_perm1730 | perm_seed1730 | pigeon_hole_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o02_size2 | 2 | 0.06092 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1730 | perm_seed1730 | vertex_color_assignment | 12 | 0.8242 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3_perm1731 | perm_seed1731 | vertex_color_assignment | 12 | 1.026 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o02_size2 | 2 | 0.02035 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o09_size2 | 2 | 0.1033 | 2.235e-08 | 2.235e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.863e-08 | 1.863e-08 | False |
| no_activity_zero_event | vertex_cover_torus | vertex_cover_torus_4x5_norat_perm1730 | perm_seed1730 | torus_vertex | 20 | 0 | 1.863e-08 | 1.863e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o10_size2 | 2 | 0.1033 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o03_size2 | 2 | 0.007285 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o08_size2 | 2 | 0.02664 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o05_size2 | 2 | 0.01011 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o03_size2 | 2 | 0.001471 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o07_size2 | 2 | 0.03784 | 1.49e-08 | 1.49e-08 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o10_size2 | 2 | 0.03447 | 1.118e-08 | 1.118e-08 | False |
| no_activity_event_nonzero | complete_coloring | k4_color3 | base | vertex_color_assignment | 12 | 1.026 | 7.451e-09 | 7.451e-09 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5 | base | dominating_set_hex_refined_o03_size2 | 2 | 0.02179 | 7.451e-09 | 7.451e-09 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1731 | perm_seed1731 | dominating_set_hex_refined_o08_size2 | 2 | 0.08525 | 7.451e-09 | 7.451e-09 | False |
| no_activity_event_nonzero | dominating_set_hex | dominating_set_hex_4x5_s5_perm1730 | perm_seed1730 | dominating_set_hex_refined_o10_size2 | 2 | 0.03314 | 7.451e-09 | 7.451e-09 | False |
| no_activity_event_nonzero | php | php_p4_h3 | base | pigeon_hole_assignment | 12 | 0.8242 | 7.451e-09 | 7.451e-09 | False |
