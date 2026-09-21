# Harder Baseline Controlled Ablation Conclusion

This combines the matched non-learned perturbation baseline with the weighted-path veto audit on the harder target manifest. It is not a new training run and does not expand the benchmark.

## Artifacts

- matched perturbation report: `docs/symmetry_harder_matched_perturbation_ablation.md`
- weighted-path veto report: `docs/symmetry_harder_weighted_path_veto.md`
- combined CSV: `runs/analysis/symmetry_harder_controlled_ablation_conclusion.csv`

## Main Conclusion

- GRPO event adapter wins harder random controls: final CPU delta -0.675143s, protocol delta -0.181831s, final CPU better on 6/7 bases.
- Matched non-learned perturbation does not reproduce that win. `matched_weight_only` random-control final CPU delta is 3.02219s; `matched_weight_phase` is 2.8618s.
- Therefore the random-control gain is not explained by a simple matched random weight/polarity perturbation. It is still generic/non-symmetry evidence, but it appears tied to learned/static/event guidance structure rather than arbitrary noise.
- Hex/torus remain weighted-path failures: GRPO final CPU delta vs plain is 5.25632s for hex and 5.99235s for torus, while adapter-minus-static final CPU is near zero.
- Offline weighted-path veto with threshold 0.05 and cap risk reduces overall protocol delta from 3.6112s to -0.0536929s by vetoing 9/20 bases.

## What This Means

- The next model objective should not reward non-symmetric random-control speedups as symmetry success.
- A deployable gate should first be a weighted-path risk veto, not a symmetry selector trained on positive examples.
- For hex/torus, improving the adapter objective alone is insufficient while neutral/static weighted paths are already near-cap or much slower than plain.
- For random controls, the useful signal is learned weighted guidance or portfolio-like behavior; it needs its own control objective if retained.

## Combined Table

| section | method | family | bases | protocol_delta_vs_plain | final_cpu_delta_vs_plain | final_cpu_delta_vs_static | better_bases_vs_plain_final_cpu | better_bases_vs_static_final_cpu | vetoed_bases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grpo_event_adapter | event_adapter_final | dominating_set_hex | 4 | 9.31651 | 5.25632 | 0.00013 | 0 | 1 | nan |
| grpo_event_adapter | event_adapter_final | random_3sat_control | 7 | -0.181831 | -0.675143 | -0.121007 | 6 | 4 | nan |
| grpo_event_adapter | event_adapter_final | vertex_cover_torus | 3 | 11.0318 | 5.99235 | -0.000388148 | 0 | 2 | nan |
| matched_nonlearned | matched_weight_only | complete_coloring | 3 | 0.0754773 | 0.0754773 | 0.20824 | 2 | 2 | nan |
| matched_nonlearned | matched_weight_only | dominating_set_hex | 4 | 5.25955 | 5.25955 | 0.00335972 | 0 | 1 | nan |
| matched_nonlearned | matched_weight_only | php | 2 | 0.196464 | 0.196464 | 0.262461 | 1 | 1 | nan |
| matched_nonlearned | matched_weight_only | random_3sat_control | 7 | 3.02219 | 3.02219 | 3.52674 | 1 | 0 | nan |
| matched_nonlearned | matched_weight_only | tseitin_complete | 1 | 0.044644 | 0.044644 | 0.0437214 | 0 | 0 | nan |
| matched_nonlearned | matched_weight_only | vertex_cover_torus | 3 | 5.9931 | 5.9931 | 0.000363704 | 0 | 1 | nan |
| matched_nonlearned | matched_weight_phase | complete_coloring | 3 | 0.108601 | 0.108601 | 0.241363 | 2 | 2 | nan |
| matched_nonlearned | matched_weight_phase | dominating_set_hex | 4 | 5.2569 | 5.2569 | 0.000708333 | 0 | 3 | nan |
| matched_nonlearned | matched_weight_phase | php | 2 | 0.201049 | 0.201049 | 0.267046 | 1 | 1 | nan |
| matched_nonlearned | matched_weight_phase | random_3sat_control | 7 | 2.8618 | 2.8618 | 3.41275 | 0 | 0 | nan |
| matched_nonlearned | matched_weight_phase | tseitin_complete | 1 | 0.0242102 | 0.0242102 | 0.0232877 | 0 | 0 | nan |
| matched_nonlearned | matched_weight_phase | vertex_cover_torus | 3 | 5.99315 | 5.99315 | 0.000412222 | 0 | 1 | nan |
| weighted_path_veto | veto_threshold_0.05_cap | complete_coloring | 3 | 0.465387 | -0.130471 | nan | nan | nan | 0 |
| weighted_path_veto | veto_threshold_0.05_cap | dominating_set_hex | 4 | 0 | 0 | nan | nan | nan | 4 |
| weighted_path_veto | veto_threshold_0.05_cap | php | 2 | 0.834991 | -0.0313906 | nan | nan | nan | 0 |
| weighted_path_veto | veto_threshold_0.05_cap | random_3sat_control | 7 | -0.601294 | -0.744898 | nan | nan | nan | 2 |
| weighted_path_veto | veto_threshold_0.05_cap | tseitin_complete | 1 | 0.0690585 | 0.00152156 | nan | nan | nan | 0 |
| weighted_path_veto | veto_threshold_0.05_cap | vertex_cover_torus | 3 | 0 | 0 | nan | nan | nan | 3 |
