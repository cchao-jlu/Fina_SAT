# Targeted v2 Mechanism Audit

## 1. Scope and Non-Claims

This targeted audit tests whether selected positive runtime cases form a plausible
mechanism chain: event identity signal -> adapter orbit separation -> final search
changes -> decisions/conflicts/final-CPU improvement. It does not train, does not
build a gate/selector, does not expand the full runtime benchmark, and does not
make a solver speedup claim.

Fixed inputs:

- attribution CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv`
- base summary CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_positive_v2_base_summary.csv`
- observations CSV: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_positive_v2_observations.csv`

## 2. Candidate Qualification

| family | base_instance_id | control_type | scale | primary_classification | qualification_tier | qualification_note | mechanism_label | repeat_rows | variants | cpu_down_rows | decisions_down_rows | conflicts_down_rows | event_identity_positive_rows | adapter_identity_positive_rows | mean_event_identity_gain_max | mean_adapter_identity_gain_max | mean_primary_delta_final_cpu | mean_primary_delta_final_decisions | mean_primary_delta_final_conflicts | mean_secondary_delta_protocol_time | targeted_audit_wall_time_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | non_symmetric_control | small | negative | control_perturbation | non-symmetric control; search change is not symmetry-specific evidence | mechanism partially aligned | 9 | 3 | 4 | 9 | 0 | 0 | 0 | 0 | 0 | -8.556e-05 | -2 | 0 | 0.003258 | 12.01 |
| dominating_set_hex | dominating_set_hex_3x6_s4 | weak_symmetry | large | negative | strong_named_runtime_regressed | primary symmetry candidate; conflicts drop in all observed rows, but current full-v2 CPU direction no longer qualifies as strict-positive | mechanism partially aligned | 9 | 3 | 3 | 6 | 9 | 9 | 9 | 4.212 | 0.4852 | 0.007801 | -1 | -2.667 | 1.147 | 12.01 |
| subset_cardinality | subset_cardinality_bw12 | weak_symmetry | large | negative | weak_named_runtime_regressed | symmetry candidate with variant-mixed search response; current full-v2 CPU direction no longer qualifies as strict-positive | mechanism partially aligned | 9 | 3 | 2 | 6 | 6 | 9 | 9 | 30.71 | 0.8094 | 0.001179 | -28.33 | -14 | 0.005966 | 12.01 |

The named candidates are retained for mechanism diagnostics. In the refreshed v2 full
runtime run used here, the two symmetry candidates no longer satisfy current
`strict_positive` qualification because final CPU is not majority-down. The audit
therefore treats them as diagnostic named targets, not as fresh runtime-positive
evidence.

## 3. Per-Repeat Join Method

For each targeted `base_instance_id + variant + repeat_id`, the script replays only
the short event-collecting warmup with the recorded `warmup_seed`, attaches the
enhanced event state, computes orbit-level event identity and adapter separation,
and joins those representation rows back to the v2 runtime deltas. The join key is
`base_instance_id + variant + repeat_id`; `event_state_hash` is recorded as the
trace/event identifier.

Orbit validity summary:

| base_instance_id | event_row_valid_reason | rows |
| --- | --- | --- |
| dominating_set_hex_3x6_s4 | orbit_size_below_min | 54 |
| dominating_set_hex_3x6_s4 | valid | 54 |
| random_3sat_control_v20_c85_seed1901 | singleton_label | 180 |
| subset_cardinality_bw12 | orbit_size_below_min | 9 |
| subset_cardinality_bw12 | static_mu_not_collapsed | 63 |
| subset_cardinality_bw12 | valid | 9 |

## 4. Dominating Set Hex Mechanism

| variant | repeat_id | event_state_l2_sum | event_identity_gain_max | adapter_identity_gain_max | event_adapter_graph_gate_evidence | primary_delta_final_cpu | primary_delta_final_decisions | primary_delta_final_conflicts | secondary_delta_protocol_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0 | 63.71 | 3.281 | 0.3216 | 1.946 | -0.01088 | -1 | -2 | 1.121 |
| base | 1 | 63.71 | 3.281 | 0.3216 | 1.946 | 0.00153 | -1 | -2 | 1.11 |
| base | 2 | 63.71 | 3.281 | 0.3216 | 1.946 | 0.05632 | -1 | -2 | 1.168 |
| perm_seed1730 | 0 | 78.41 | 3.906 | 0.5371 | 2.197 | -0.01581 | 2 | -2 | 1.166 |
| perm_seed1730 | 1 | 78.41 | 3.906 | 0.5371 | 2.197 | -0.02547 | 2 | -2 | 1.134 |
| perm_seed1730 | 2 | 78.41 | 3.906 | 0.5371 | 2.197 | 0.0079 | 2 | -2 | 1.134 |
| perm_seed1731 | 0 | 86.05 | 5.449 | 0.5971 | 2.303 | 0.02613 | -4 | -4 | 1.184 |
| perm_seed1731 | 1 | 86.05 | 5.449 | 0.5971 | 2.303 | 0.02047 | -4 | -4 | 1.169 |
| perm_seed1731 | 2 | 86.05 | 5.449 | 0.5971 | 2.303 | 0.01002 | -4 | -4 | 1.137 |

Conclusion: `dominating_set_hex_3x6_s4` is `mechanism partially aligned` under the refreshed v2 runtime rows.
Conflicts drop in all nine rows, event identity is positive on valid orbit rows,
and adapter separation is present. CPU does not move in the same direction on a
majority of rows, and the `perm_seed1730` variant has decision increases, so the
evidence is conflicts-driven and only partial. Protocol time still loses against
static because event collection overhead is much larger than the local final-solve
gain.

## 5. Subset Cardinality Variant Diagnosis

| base_instance_id | variant | repeat_rows | cpu_down_rows | decisions_down_rows | decisions_up_rows | conflicts_down_rows | conflicts_up_rows | mean_event_l2 | mean_gate_evidence | gate_open_rows | mean_event_identity_gain_max | mean_adapter_identity_gain_max | mean_warmup_decisions | mean_warmup_conflicts | mean_primary_delta_final_cpu | mean_primary_delta_final_decisions | mean_primary_delta_final_conflicts | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subset_cardinality_bw12 | base | 3 | 2 | 3 | 0 | 3 | 0 | 3623 | 4.804 | 3 | 15.26 | 0.9309 | 384 | 312 | -0.000621 | -55 | -22 | variant_search_improved |
| subset_cardinality_bw12 | perm_seed1730 | 3 | 0 | 0 | 3 | 0 | 3 | 3254 | 4.796 | 3 | 41.06 | 0.7796 | 341 | 292 | 0.001565 | 13 | 1 | variant_search_worse_over_adaptation_or_perm_nonrobust |
| subset_cardinality_bw12 | perm_seed1731 | 3 | 0 | 3 | 0 | 3 | 0 | 3282 | 4.663 | 3 | 35.81 | 0.7178 | 356 | 285 | 0.002592 | -43 | -21 | variant_search_improved |

| variant | repeat_id | event_state_l2_sum | event_identity_gain_max | adapter_identity_gain_max | warmup_decisions | warmup_conflicts | primary_delta_final_cpu | primary_delta_final_decisions | primary_delta_final_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0 | 3623 | 15.26 | 0.9309 | 384 | 312 | 0.000296 | -55 | -22 |
| base | 1 | 3623 | 15.26 | 0.9309 | 384 | 312 | -0.000171 | -55 | -22 |
| base | 2 | 3623 | 15.26 | 0.9309 | 384 | 312 | -0.001988 | -55 | -22 |
| perm_seed1730 | 0 | 3254 | 41.06 | 0.7796 | 341 | 292 | 0.001036 | 13 | 1 |
| perm_seed1730 | 1 | 3254 | 41.06 | 0.7796 | 341 | 292 | 0.001761 | 13 | 1 |
| perm_seed1730 | 2 | 3254 | 41.06 | 0.7796 | 341 | 292 | 0.001898 | 13 | 1 |
| perm_seed1731 | 0 | 3282 | 35.81 | 0.7178 | 356 | 285 | 0.003494 | -43 | -21 |
| perm_seed1731 | 1 | 3282 | 35.81 | 0.7178 | 356 | 285 | 0.001964 | -43 | -21 |
| perm_seed1731 | 2 | 3282 | 35.81 | 0.7178 | 356 | 285 | 0.002317 | -43 | -21 |

Conclusion: `subset_cardinality_bw12` is mechanism partially aligned and
variant-mixed. The base and `perm_seed1731` variants show large search reductions,
but `perm_seed1730` consistently worsens decisions/conflicts despite strong event
L2, open graph gate, and nonzero adapter separation. That points to permutation
non-robustness or over-adaptation in the adapter objective rather than a clean
family-level mechanism.

## 6. Random Control Check

| family | base_instance_id | variant | repeat_rows | decisions_down_rows | conflicts_down_rows | cpu_down_rows | mean_event_identity_gain_max | mean_adapter_identity_gain_max | mean_primary_delta_final_decisions | mean_primary_delta_final_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | base | 3 | 3 | 0 | 1 | 0 | 0 | -2 | -0.000591 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1730 | 3 | 3 | 0 | 1 | 0 | 0 | -2 | 0.0004077 |
| random_3sat_control | random_3sat_control_v20_c85_seed1901 | perm_seed1731 | 3 | 3 | 0 | 2 | 0 | 0 | -2 | -7.333e-05 |

| variant | repeat_id | event_state_l2_sum | event_identity_gain_max | adapter_identity_gain_max | primary_delta_final_cpu | primary_delta_final_decisions | primary_delta_final_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 0 | 33.86 | 0 | 0 | -0.002855 | -2 | 0 |
| base | 1 | 33.86 | 0 | 0 | 0.000139 | -2 | 0 |
| base | 2 | 33.86 | 0 | 0 | 0.000943 | -2 | 0 |
| perm_seed1730 | 0 | 33.84 | 0 | 0 | 0.000704 | -2 | 0 |
| perm_seed1730 | 1 | 33.84 | 0 | 0 | -0.002369 | -2 | 0 |
| perm_seed1730 | 2 | 33.84 | 0 | 0 | 0.002888 | -2 | 0 |
| perm_seed1731 | 0 | 33.83 | 0 | 0 | -0.00035 | -2 | 0 |
| perm_seed1731 | 1 | 33.83 | 0 | 0 | -6.9e-05 | -2 | 0 |
| perm_seed1731 | 2 | 33.83 | 0 | 0 | 0.000199 | -2 | 0 |

Conclusion: the random 3SAT control shows adapter-induced search perturbation
without symmetry-specific evidence. It must stay separate from symmetry-positive
claims.

## 7. Decision and Next Step

- Dominating hex: `strong_named_runtime_regressed` and `mechanism partially aligned`; do not expand to gate/selector. Recheck nearby hex only after runtime qualification is stable.
- Subset cardinality: `weak_named_runtime_regressed` and `mechanism partially aligned`; investigate permutation robustness/objective before broader runtime work.
- Random control: generic perturbation exists; do not treat search changes alone as symmetry benefit.
- Full gate/selector remains postponed until multiple symmetry families show stable aligned mechanisms and event overhead has a credible reduction path.
