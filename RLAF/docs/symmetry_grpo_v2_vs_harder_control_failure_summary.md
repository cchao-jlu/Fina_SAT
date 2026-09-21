# GRPO v2 vs Harder Baseline Failure Diagnosis

This combines the original v2 GRPO runtime validation with the new harder-baseline validation. It is a post-hoc analysis only: no training, no gate, and no benchmark expansion beyond the run already produced.

## Artifacts

- combined CSV: `runs/analysis/symmetry_grpo_v2_vs_harder_control_failure_summary.csv`
- v2 detail: `docs/symmetry_grpo_v2_control_vs_symmetry_failure.md`
- harder detail: `docs/symmetry_grpo_harder_control_vs_symmetry_failure.md`

## Main Read

- Harder baseline changes the picture from “no visible runtime win” to “adapter/weighted guidance can produce real final-solve wins on hard random controls.”
- On harder random controls, adapter final CPU beats plain on 6/7 bases and mean final CPU delta is -0.675143s.
- The same harder random controls have mean protocol delta -0.181831s, so overhead is no longer always fatal on controls.
- For dominating_set_hex and vertex_cover_torus, final CPU remains much worse than plain: mean deltas are 5.25632s and 5.99235s.
- For hex/torus, adapter-minus-static final CPU is near zero (0.00013s, -0.000388148s). The dominant failure is not adapter inference; it is weighted/binary path plus event collection overhead.
- Hex/torus cap risk is high on harder baseline: 3/4 hex bases and 3/3 torus bases have adapter final CPU near the 10s cap.

## Why Random Controls Win

- The parameter-shift replay shows large weight perturbations on random controls: mean absolute weight delta is roughly 0.65-1.20 on harder controls, with max weight ratio near 2.718.
- Phase flips are small but nonzero on several harder controls. The bigger signal is weight re-ranking/amplification, not broad polarity flipping.
- Because these are non-symmetric controls, this is best interpreted as generic weighted-search perturbation or restart-like diversification, not symmetry-specific learning.

## Why Hex/Torus Lose

- Event collection overhead is 4-5s on the harder hex/torus bases, often by itself larger than any adapter final-solve change.
- Weighted Glucose path is also risky on these families: weighted binary input delta is strongly positive in the harder attribution table, pushing many rows close to the 10s cap.
- Adapter final solve relative to static weighted is near neutral. That means the current GRPO adapter is not fixing the family-level weighted-path pathology.

## Combined Family Summary

| run | family | bases | mean_adapter_minus_plain_protocol | mean_adapter_minus_plain_final_cpu | mean_adapter_minus_static_final_cpu | mean_cached_minus_static_protocol | final_solve_better_than_plain_bases | final_solve_better_than_static_bases | final_solve_worse_than_static_bases | cap_risk_bases | mean_warmup_cpu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| harder_baseline | dominating_set_hex | 4 | 9.31651 | 5.25632 | 0.00013 | 4.03168 | 0 | 1 | 3 | 3 | 4.03099 |
| harder_baseline | random_3sat_control | 7 | -0.181831 | -0.675143 | -0.121007 | 0.482915 | 6 | 4 | 3 | 0 | 0.481963 |
| harder_baseline | vertex_cover_torus | 3 | 11.0318 | 5.99235 | -0.000388148 | 4.99786 | 0 | 2 | 1 | 3 | 4.9972 |
| v2 | dominating_set_hex | 4 | 3.78855 | 0.914971 | -0.00267697 | 2.79112 | 0 | 3 | 1 | 2 | 2.79046 |
| v2 | random_3sat_control | 7 | 0.012989 | 0.00102292 | 0.000640635 | 0.00322303 | 1 | 2 | 5 | 0 | 0.00253667 |
| v2 | vertex_cover_torus | 7 | 2.45122 | 0.120393 | -0.000121048 | 2.27939 | 0 | 3 | 4 | 3 | 2.27875 |

## Random Control Parameter Shift Summary

| run | bases | mean_adapter_minus_plain_final_cpu | mean_adapter_minus_static_final_cpu | final_solve_better_than_plain_bases | final_solve_better_than_static_bases | phase_flip_frac_mean | weight_delta_abs_mean | weight_ratio_mean | weight_ratio_max | weight_rank_spearman_mean | event_l2_weight_abs_delta_spearman_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v2 | 7 | 0.00102292 | 0.000640635 | 1 | 2 | 0.0119048 | 0.579133 | 1.1022 | 2.71864 | 0.552531 | 0.293941 |
| harder_baseline | 7 | -0.675143 | -0.121007 | 6 | 4 | 0.0141328 | 0.858865 | 1.30701 | 2.71896 | 0.603362 | 0.26694 |

## Next Step

Do not expand benchmark yet. The next experiment should be a controlled ablation on the harder target manifest:

1. Run static weighted vs plain with event path disabled, grouped by family, to isolate weighted-binary risk.
2. Run adapter final with a no-event-cost oracle accounting view: compare only final CPU against static/cached, not protocol time.
3. For random controls, add a non-learned perturbation baseline with matched weight-delta distribution. If it matches the wins, the GRPO effect is generic perturbation.
4. For hex/torus, test a conservative weighted-path veto before any selector training: disable weighted/event path when neutral/static weighted is near cap or much slower than plain in calibration.

Current conclusion: harder baseline proves acceleration potential under weighted perturbation, but the evidence is not SAT-symmetry-specific. It points to a perturbation/portfolio effect on random controls and a weighted-path failure on hex/torus.
