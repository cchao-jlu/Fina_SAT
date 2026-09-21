# Matched Non-Learned Perturbation Ablation

This runs weighted Glucose with non-learned variable weights matched to the observed GRPO random-control adapter perturbation scale. It is a controlled ablation, not training and not a speedup claim.

## Artifacts

- per-instance CSV: `runs/analysis/symmetry_harder_matched_perturbation_per_instance.csv`
- base summary CSV: `runs/analysis/symmetry_harder_matched_perturbation_by_base.csv`
- family summary CSV: `runs/analysis/symmetry_harder_matched_perturbation_by_family.csv`

## Random-Control Readout

| method | family | bases | mean_delta_vs_plain_unguided_glucose_final_cpu_time | better_bases_vs_plain_unguided_glucose_final_cpu_time | mean_delta_vs_plain_unguided_glucose_protocol_accounted_time | better_bases_vs_plain_unguided_glucose_protocol_accounted_time | mean_delta_vs_event_adapter_final_final_cpu_time | better_bases_vs_event_adapter_final_final_cpu_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| matched_weight_only | random_3sat_control | 7 | 3.02219 | 1 | 3.02219 | 1 | 3.64789 | 0 |
| matched_weight_phase | random_3sat_control | 7 | 2.8618 | 0 | 2.8618 | 0 | 3.52367 | 0 |

## Family Summary

| method | family | bases | mean_delta_vs_plain_unguided_glucose_final_cpu_time | better_bases_vs_plain_unguided_glucose_final_cpu_time | mean_delta_vs_plain_unguided_glucose_protocol_accounted_time | better_bases_vs_plain_unguided_glucose_protocol_accounted_time | mean_delta_vs_event_adapter_final_final_cpu_time | better_bases_vs_event_adapter_final_final_cpu_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| matched_weight_only | complete_coloring | 3 | 0.0754773 | 2 | 0.0754773 | 2 | 0.205948 | 2 |
| matched_weight_only | dominating_set_hex | 4 | 5.25955 | 0 | 5.25955 | 0 | 0.00322972 | 1 |
| matched_weight_only | php | 2 | 0.196464 | 1 | 0.196464 | 1 | 0.227854 | 1 |
| matched_weight_only | random_3sat_control | 7 | 3.02219 | 1 | 3.02219 | 1 | 3.64789 | 0 |
| matched_weight_only | tseitin_complete | 1 | 0.044644 | 0 | 0.044644 | 0 | 0.0431224 | 0 |
| matched_weight_only | vertex_cover_torus | 3 | 5.9931 | 0 | 5.9931 | 0 | 0.000751852 | 0 |
| matched_weight_phase | complete_coloring | 3 | 0.108601 | 2 | 0.108601 | 2 | 0.239072 | 2 |
| matched_weight_phase | dominating_set_hex | 4 | 5.2569 | 0 | 5.2569 | 0 | 0.000578333 | 2 |
| matched_weight_phase | php | 2 | 0.201049 | 1 | 0.201049 | 1 | 0.232439 | 1 |
| matched_weight_phase | random_3sat_control | 7 | 2.8618 | 0 | 2.8618 | 0 | 3.52367 | 0 |
| matched_weight_phase | tseitin_complete | 1 | 0.0242102 | 0 | 0.0242102 | 0 | 0.0226887 | 0 |
| matched_weight_phase | vertex_cover_torus | 3 | 5.99315 | 0 | 5.99315 | 0 | 0.00080037 | 1 |

## Interpretation Guide

- If matched perturbation wins random controls similarly to GRPO, the current GRPO gain is likely generic weighted-search perturbation.
- If matched perturbation does not win random controls, learned static/event structure is doing something beyond a simple matched random perturbation.
- `matched_weight_only` changes weights only and keeps all positive neutral phase.
- `matched_weight_phase` adds a small matched phase-flip rate on top of the weight perturbation.
