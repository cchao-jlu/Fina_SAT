# EchoSAT Symmetry GRPO v1.4 Reward Replay Audit

This audit does not train, rerun solver rollouts, expand benchmarks, or add a gate/selector.

## Artifacts

- source inventory: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_source_inventory.csv`
- proxy replay table: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_proxy_table.csv`
- role summary: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_role_summary.csv`
- base summary: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_base_summary.csv`
- positive advantage failures: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_positive_advantage_failures.csv`
- group sampling iterations: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_group_sampling_iterations.csv`
- group sampling summary: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_group_sampling_summary.csv`
- group integrity: `runs/analysis/echosat_symmetry_grpo_v1_4_reward_replay_group_integrity.csv`

## Source Availability

| artifact | path | exists | size_bytes | usable_for_per_sample_training_replay |
| --- | --- | --- | --- | --- |
| run_training_config | runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/training_config.yaml | True | 6018 | False |
| run_config | runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/config.yaml | True | 2937 | False |
| hydra_config | outputs/2026-06-22/18-25-41/.hydra/config.yaml | True | 5918 | False |
| hydra_overrides | outputs/2026-06-22/18-25-41/.hydra/overrides.yaml | True | 3 | False |
| hydra_train_log | outputs/2026-06-22/18-25-41/train_rlaf.log | True | 0 | False |
| run_solver_stats | runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/solver_stats.csv | False | 0 | False |
| run_training_solver_stats | runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/training_solver_stats.csv | False | 0 | False |
| run_reward_replay | runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_4_WC1_StrictBest/reward_replay.csv | False | 0 | False |

- raw per-sample training solver_stats recoverable: `False`
- Hydra train log size: `0` bytes
- Because v1.4 did not persist per-iteration `solver_stats` and wandb was disabled, exact historical training-batch reward replay is not recoverable from disk. The replay below is a proxy over existing targeted acceptance rows using the current v1.4 reward/advantage equations.

## Key Code-Level Findings

- Current `symmetry_grpo_v1_4` reward code uses `static_weighted_glucose` final solve as the search-work baseline. In the current runtime protocol, `cached_trace_no_adapter_final` reuses the static final solve, so adapter-vs-cached and adapter-vs-static final decisions/conflicts are equivalent in these acceptance rows.
- GRPO normalization is by `cnf_id`, not by `base_instance_id`, `formula_equivalence_group`, or `echosat_sampling_group_id`. Paired variants can be selected in the same iteration, but they do not share the GRPO mean/std normalization group.
- In the v1.4 branch, controls receive `echosat_advantage_weight = 1.0` before the positive-advantage upper-bound clamp, even though config has `echosat_control_advantage_weight: 0.0`. The clamp prevents positive control advantages in this proxy, but controls still carry negative gradients.
- Parameter-shift diagnostics are not available in the acceptance rows, so this proxy sets perturbation-derived penalties to zero. That underestimates control/phase-shift penalties relative to an exact live training batch.

## Proxy Replay Scope

- rows: `810`
- checkpoints: `iter=0, iter=15`
- warmup conflicts: `1, 3, 5`

## Role Advantage Summary

| checkpoint | warmup_conflicts | target_role | rows | static_search_ok_frac | cached_search_ok_frac | positive_allowed_frac | reward_mean | raw_positive_advantage_frac | weighted_positive_before_clamp_frac | final_positive_advantage_frac | positive_advantage_clamped_rows | anchor_failure_penalty_mean | hard_negative_penalty_mean | random_control_penalty_mean | direction_penalty_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | anchor | 18 | 1 | 1 | 1 | 0.117436 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| iter=0 | 1 | hard_negative | 18 | 0.333333 | 0.333333 | 0 | -36.5805 | 0 | 0 | 0 | 0 | 0 | 5.97296 | 0 | 6.01738 |
| iter=0 | 1 | other | 27 | 0.222222 | 0.222222 | 0 | -118.326 | 0.481481 | 0.481481 | 0 | 13 | 0 | 0 | 0 | 0.84045 |
| iter=0 | 1 | random_control | 63 | 0 | 0 | 0 | -19.7794 | 0.126984 | 0.126984 | 0 | 8 | 0 | 0 | 3.20943 | 0 |
| iter=0 | 1 | subset_failure | 3 | 0 | 0 | 0 | -685.216 | 0.666667 | 0.666667 | 0 | 2 | 0 | 0.966875 | 0 | 0 |
| iter=0 | 1 | subset_other | 6 | 0 | 0 | 0 | -4.33884 | 0.5 | 0.5 | 0 | 3 | 0 | 0.374174 | 0 | 0 |
| iter=0 | 3 | anchor | 18 | 1 | 1 | 1 | 0.0640052 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| iter=0 | 3 | hard_negative | 18 | 0 | 0 | 0 | -7.9144 | 0 | 0 | 0 | 0 | 0 | 2.1308 | 0 | 0 |
| iter=0 | 3 | other | 27 | 0.444444 | 0.444444 | 0.296296 | -125.599 | 0.37037 | 0.37037 | 0.0740741 | 8 | 0 | 0 | 0 | 0.696183 |
| iter=0 | 3 | random_control | 63 | 0.0952381 | 0.0952381 | 0 | -17.9088 | 0.126984 | 0.126984 | 0 | 8 | 0 | 0 | 2.82328 | 0.216765 |
| iter=0 | 3 | subset_failure | 3 | 0 | 0 | 0 | -20.0597 | 0.666667 | 0.666667 | 0 | 2 | 0 | 3.61407 | 0 | 2.89126 |
| iter=0 | 3 | subset_other | 6 | 0.5 | 0.5 | 0 | -7.31073 | 0 | 0 | 0 | 0 | 0 | 1.1874 | 0 | 1.19526 |
| iter=0 | 5 | anchor | 18 | 1 | 1 | 1 | 0.0844971 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| iter=0 | 5 | hard_negative | 18 | 0 | 0 | 0 | -5.30025 | 0 | 0 | 0 | 0 | 0 | 1.42699 | 0 | 0 |
| iter=0 | 5 | other | 27 | 0.555556 | 0.555556 | 0.296296 | -85.9256 | 0.481481 | 0.481481 | 0.0740741 | 11 | 0 | 0 | 0 | 1.15669 |
| iter=0 | 5 | random_control | 63 | 0.142857 | 0.142857 | 0 | -17.533 | 0.15873 | 0.15873 | 0 | 10 | 0 | 0 | 2.85949 | 0 |
| iter=0 | 5 | subset_failure | 3 | 0 | 0 | 0 | -26.661 | 0.666667 | 0.666667 | 0 | 2 | 0 | 4.7548 | 0 | 3.80384 |
| iter=0 | 5 | subset_other | 6 | 0.5 | 0.5 | 0 | -3.3125 | 0.333333 | 0.333333 | 0 | 2 | 0 | 0.41892 | 0 | 0.581376 |
| iter=15 | 1 | anchor | 18 | 0.666667 | 0.666667 | 0 | -2.06386 | 0 | 0 | 0 | 0 | 0.0933218 | 0 | 0 | 0.62336 |
| iter=15 | 1 | hard_negative | 18 | 0.333333 | 0.333333 | 0 | -28.3494 | 0 | 0 | 0 | 0 | 0 | 4.61906 | 0 | 4.67364 |
| iter=15 | 1 | other | 27 | 0.222222 | 0.222222 | 0 | -130.795 | 0.333333 | 0.333333 | 0 | 9 | 0 | 0 | 0 | 0.694752 |
| iter=15 | 1 | random_control | 63 | 0.142857 | 0.142857 | 0 | -16.9633 | 0.126984 | 0.126984 | 0 | 8 | 0 | 0 | 2.77649 | 0 |
| iter=15 | 1 | subset_failure | 3 | 0 | 0 | 0 | -1127.8 | 0.666667 | 0.666667 | 0 | 2 | 0 | 0.630978 | 0 | 0 |
| iter=15 | 1 | subset_other | 6 | 0 | 0 | 0 | -1.92076 | 0 | 0 | 0 | 0 | 0 | 0.517127 | 0 | 0 |
| iter=15 | 3 | anchor | 18 | 1 | 1 | 1 | 0.101823 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| iter=15 | 3 | hard_negative | 18 | 0 | 0 | 0 | -5.3 | 0 | 0 | 0 | 0 | 0 | 1.42692 | 0 | 0 |
| iter=15 | 3 | other | 27 | 0.333333 | 0.333333 | 0.296296 | -60.2177 | 0.407407 | 0.407407 | 0.0740741 | 9 | 0 | 0 | 0 | 0 |
| iter=15 | 3 | random_control | 63 | 0.142857 | 0.142857 | 0 | -17.5486 | 0.142857 | 0.142857 | 0 | 9 | 0 | 0 | 2.86453 | 0 |
| iter=15 | 3 | subset_failure | 3 | 0 | 0 | 0 | -4.31827 | 0.666667 | 0.666667 | 0 | 2 | 0 | 0.940755 | 0 | 0 |
| iter=15 | 3 | subset_other | 6 | 0 | 0 | 0 | -2.88377 | 0.5 | 0.5 | 0 | 3 | 0 | 0.303425 | 0 | 0 |
| iter=15 | 5 | anchor | 18 | 1 | 1 | 1 | 0.0967739 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| iter=15 | 5 | hard_negative | 18 | 0 | 0 | 0 | -6.7305 | 0 | 0 | 0 | 0 | 0 | 1.81206 | 0 | 0 |
| iter=15 | 5 | other | 27 | 0.555556 | 0.555556 | 0.185185 | -70.8822 | 0.481481 | 0.481481 | 0.185185 | 8 | 0 | 0 | 0 | 1.15673 |
| iter=15 | 5 | random_control | 63 | 0.142857 | 0.142857 | 0 | -17.6107 | 0.126984 | 0.126984 | 0 | 8 | 0 | 0 | 2.87415 | 0 |
| iter=15 | 5 | subset_failure | 3 | 0 | 0 | 0 | -3.60341 | 0 | 0 | 0 | 0 | 0 | 0.970149 | 0 | 0 |
| iter=15 | 5 | subset_other | 6 | 0 | 0 | 0 | -1.01753 | 0.666667 | 0.666667 | 0 | 4 | 0 | 0.211412 | 0 | 0 |

## Target Base Summary

| checkpoint | warmup_conflicts | target_role | family | base_instance_id | rows | static_search_ok_frac | cached_search_ok_frac | raw_positive_advantage_frac | final_positive_advantage_frac | positive_advantage_clamped_rows | reward_mean | static_decisions_delta_mean | cached_decisions_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | anchor | complete_coloring | k9_color8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.117436 | -5381.33 | -5381.33 |
| iter=0 | 1 | anchor | php | php_p9_h8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.117436 | -5381.33 | -5381.33 |
| iter=0 | 1 | hard_negative | complete_coloring | k10_color9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | -36.5805 | 102.333 | 102.333 |
| iter=0 | 1 | hard_negative | php | php_p10_h9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | -36.5805 | 102.333 | 102.333 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0 | 0 | 0 | -3.64167 | 636 | 636 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 41088 | 41088 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 277 | 277 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -15.2035 | 13512 | 13512 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0 | 0 | 0.333333 | 0 | 3 | -20.7575 | 34381.3 | 34381.3 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.555556 | 0 | 5 | -8.85353 | 55937.3 | 55937.3 |
| iter=0 | 1 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 2240 | 2240 |
| iter=0 | 1 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0 | 0 | 0.555556 | 0 | 5 | -231.298 | 26.3333 | 26.3333 |
| iter=0 | 3 | anchor | complete_coloring | k9_color8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0640052 | -2988.33 | -2988.33 |
| iter=0 | 3 | anchor | php | php_p9_h8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0640052 | -2988.33 | -2988.33 |
| iter=0 | 3 | hard_negative | complete_coloring | k10_color9 | 9 | 0 | 0 | 0 | 0 | 0 | -7.9144 | 81117.7 | 81117.7 |
| iter=0 | 3 | hard_negative | php | php_p10_h9 | 9 | 0 | 0 | 0 | 0 | 0 | -7.9144 | 81117.7 | 81117.7 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0.222222 | 0 | 2 | -4.57525 | 772 | 772 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 14538 | 14538 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 321 | 321 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -16.7986 | 14848.7 | 14848.7 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.666667 | 0.666667 | 0.222222 | 0 | 2 | -5.61075 | -18003 | -18003 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.444444 | 0 | 4 | -8.37679 | 52820 | 52820 |
| iter=0 | 3 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 2549.33 | 2549.33 |
| iter=0 | 3 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0.333333 | 0.333333 | 0.222222 | 0 | 2 | -11.5604 | 16.6667 | 16.6667 |
| iter=0 | 5 | anchor | complete_coloring | k9_color8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0844971 | -3834.67 | -3834.67 |
| iter=0 | 5 | anchor | php | php_p9_h8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0844971 | -3834.67 | -3834.67 |
| iter=0 | 5 | hard_negative | complete_coloring | k10_color9 | 9 | 0 | 0 | 0 | 0 | 0 | -5.29979 | 51388.3 | 51388.3 |
| iter=0 | 5 | hard_negative | php | php_p10_h9 | 9 | 0 | 0 | 0 | 0 | 0 | -5.30071 | 51238.3 | 51238.3 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0.222222 | 0 | 2 | -3.35642 | 602.667 | 602.667 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 12513.7 | 12513.7 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 284.667 | 284.667 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -18.9038 | 16639 | 16639 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 1 | 1 | 0.333333 | 0 | 3 | -1.00324 | -29459.7 | -29459.7 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.555556 | 0 | 5 | -9.46734 | 59396.7 | 59396.7 |
| iter=0 | 5 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 1892 | 1892 |
| iter=0 | 5 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0.333333 | 0.333333 | 0.444444 | 0 | 4 | -11.0953 | 6.33333 | 6.33333 |
| iter=15 | 1 | anchor | complete_coloring | k9_color8 | 9 | 0.666667 | 0.666667 | 0 | 0 | 0 | -2.06386 | -2902 | -2902 |
| iter=15 | 1 | anchor | php | php_p9_h8 | 9 | 0.666667 | 0.666667 | 0 | 0 | 0 | -2.06386 | -2902 | -2902 |
| iter=15 | 1 | hard_negative | complete_coloring | k10_color9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | -28.3494 | -548.667 | -548.667 |
| iter=15 | 1 | hard_negative | php | php_p10_h9 | 9 | 0.333333 | 0.333333 | 0 | 0 | 0 | -28.3494 | -548.667 | -548.667 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0.222222 | 0 | 2 | -4.00759 | 688 | 688 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 37663.3 | 37663.3 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 375 | 375 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -16.0942 | 14268.3 | 14268.3 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 1 | 1 | 0.222222 | 0 | 2 | -0.71282 | -18201 | -18201 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.444444 | 0 | 4 | -7.92823 | 50224.3 | 50224.3 |
| iter=15 | 1 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 2273.33 | 2273.33 |
| iter=15 | 1 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0 | 0 | 0.222222 | 0 | 2 | -377.214 | 24 | 24 |
| iter=15 | 3 | anchor | complete_coloring | k9_color8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.101823 | -4750.67 | -4750.67 |
| iter=15 | 3 | anchor | php | php_p9_h8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.101823 | -4750.67 | -4750.67 |
| iter=15 | 3 | hard_negative | complete_coloring | k10_color9 | 9 | 0 | 0 | 0 | 0 | 0 | -5.32691 | 53641 | 53641 |
| iter=15 | 3 | hard_negative | php | php_p10_h9 | 9 | 0 | 0 | 0 | 0 | 0 | -5.27309 | 52816 | 52816 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0 | 0 | 0 | -5.40697 | 907 | 907 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 13014 | 13014 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 348.333 | 348.333 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -16.4357 | 14522.7 | 14522.7 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 1 | 1 | 0.333333 | 0 | 3 | -0.751504 | -20565.3 | -20565.3 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.666667 | 0 | 6 | -10.2461 | 64129.7 | 64129.7 |
| iter=15 | 3 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 2288 | 2288 |
| iter=15 | 3 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0 | 0 | 0.555556 | 0 | 5 | -3.36194 | 26 | 26 |
| iter=15 | 5 | anchor | complete_coloring | k9_color8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0967739 | -4368 | -4368 |
| iter=15 | 5 | anchor | php | php_p9_h8 | 9 | 1 | 1 | 0 | 0 | 0 | 0.0967739 | -4368 | -4368 |
| iter=15 | 5 | hard_negative | complete_coloring | k10_color9 | 9 | 0 | 0 | 0 | 0 | 0 | -6.7305 | 65424.7 | 65424.7 |
| iter=15 | 5 | hard_negative | php | php_p10_h9 | 9 | 0 | 0 | 0 | 0 | 0 | -6.7305 | 65424.7 | 65424.7 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0 | 0 | 0 | 0 | 0 | -4.34179 | 742.667 | 742.667 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 13993.7 | 13993.7 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 309.333 | 309.333 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0 | 0 | 0 | 0 | 0 | -18.841 | 16617.3 | 16617.3 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 1 | 1 | 0.333333 | 0 | 3 | -0.981412 | -29296.3 | -29296.3 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0 | 0 | 0.555556 | 0 | 5 | -9.11063 | 56734.3 | 56734.3 |
| iter=15 | 5 | random_control | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0 | 0 | 0 | 0 | 0 | -30 | 2161.33 | 2161.33 |
| iter=15 | 5 | subset_failure,subset_other | subset_cardinality | subset_cardinality_bw12 | 9 | 0 | 0 | 0.444444 | 0 | 4 | -1.87949 | 20.3333 | 20.3333 |

## Positive Advantage Failure Rows

| checkpoint | warmup_conflicts | family | base_instance_id | variant | repeat_id | target_role | static_search_ok | cached_search_ok | echosat_positive_allowed | echosat_reward_proxy | grpo_group_mean_cost_proxy | grpo_group_std_cost_proxy | grpo_raw_advantage_proxy | echosat_advantage_weight_proxy | grpo_weighted_advantage_proxy_before_clamp | echosat_advantage_upper_bound_proxy | grpo_final_advantage_proxy | positive_advantage_clamped_to_zero | echosat_anchor_failure_penalty | echosat_hard_negative_penalty | echosat_random_control_penalty | echosat_direction_consistency_penalty | static_adapter_decisions_delta | static_adapter_conflicts_delta | adapter_cached_decisions_delta | adapter_cached_conflicts_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | False | False | False | -16.6391 | 16.7125 | 0.0638923 | 1.14982 | 1 | 1.14982 | 0 | 0 | True | 0 | 0 | 2.51102 | 0 | 31246 | 26789 | 31246 | 26789 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | False | False | False | -32.4173 | 32.4178 | 0.0193835 | 0.0288045 | 1 | 0.0288045 | 0 | 0 | True | 0 | 0 | 4.62034 | 0 | 44978 | 39848 | 44978 | 39848 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | random_control | False | False | False | -32.3987 | 32.4178 | 0.0193835 | 0.985286 | 1 | 0.985286 | 0 | 0 | True | 0 | 0 | 4.62034 | 0 | 44978 | 39848 | 44978 | 39848 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 1 | random_control | False | False | False | -7.07426 | 7.07767 | 0.00695774 | 0.489907 | 1 | 0.489907 | 0 | 0 | True | 0 | 0 | 0.964701 | 0 | 47572 | 36063 | 47572 | 36063 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 2 | random_control | False | False | False | -7.07307 | 7.07767 | 0.00695774 | 0.66058 | 1 | 0.66058 | 0 | 0 | True | 0 | 0 | 0.964701 | 0 | 47572 | 36063 | 47572 | 36063 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 1 | random_control | False | False | False | -10.1687 | 10.1806 | 0.0103964 | 1.14286 | 1 | 1.14286 | 0 | 0 | True | 0 | 0 | 1.40781 | 0 | 61097 | 49646 | 61097 | 49646 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 1 | random_control | False | False | False | -9.30123 | 9.30234 | 0.0230937 | 0.0479568 | 1 | 0.0479568 | 0 | 0 | True | 0 | 0 | 1.28133 | 0 | 59143 | 47437 | 59143 | 47437 |
| iter=0 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 2 | random_control | False | False | False | -9.27982 | 9.30234 | 0.0230937 | 0.975158 | 1 | 0.975158 | 0 | 0 | True | 0 | 0 | 1.28133 | 0 | 59143 | 47437 | 59143 | 47437 |
| iter=0 | 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_failure | False | False | False | -3.59125 | 685.216 | 1180.61 | 0.57735 | 0.5921 | 0.341849 | 0 | 0 | True | 0 | 0.966875 | 0 | 0 | 41 | 42 | 41 | 42 |
| iter=0 | 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_failure | False | False | False | -3.59125 | 685.216 | 1180.61 | 0.57735 | 0.5921 | 0.341849 | 0 | 0 | True | 0 | 0.966875 | 0 | 0 | 41 | 42 | 41 | 42 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 0 | random_control | False | False | False | -3.4548 | 3.4887 | 0.0587246 | 0.57735 | 1 | 0.57735 | 0 | 0 | True | 0 | 0 | 0.5758 | 0 | 600 | 450 | 600 | 450 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 2 | random_control | False | False | False | -3.4548 | 3.4887 | 0.0587246 | 0.57735 | 1 | 0.57735 | 0 | 0 | True | 0 | 0 | 0.5758 | 0 | 600 | 450 | 600 | 450 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | True | True | False | -7.91698 | 7.99132 | 0.0687892 | 1.08076 | 1 | 1.08076 | 0 | 0 | True | 0 | 0 | 0 | 2.0446 | -30524 | -28419 | -30524 | -28419 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | False | False | False | -3.59409 | 3.598 | 0.00350845 | 1.1154 | 1 | 1.1154 | 0 | 0 | True | 0 | 0 | 0.148148 | 0.829626 | 1581 | 1154 | 1581 | 1154 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 1 | random_control | False | False | False | -5.20777 | 5.2268 | 0.0176097 | 1.0808 | 1 | 1.0808 | 0 | 0 | True | 0 | 0 | 0.709913 | 0 | 35594 | 26006 | 35594 | 26006 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 1 | random_control | False | False | False | -11.8558 | 11.8622 | 0.00747252 | 0.857251 | 1 | 0.857251 | 0 | 0 | True | 0 | 0 | 1.6492 | 0 | 71305 | 58401 | 71305 | 58401 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 2 | random_control | False | False | False | -11.8604 | 11.8622 | 0.00747252 | 0.241328 | 1 | 0.241328 | 0 | 0 | True | 0 | 0 | 1.6492 | 0 | 71305 | 58401 | 71305 | 58401 |
| iter=0 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 2 | random_control | False | False | False | -8.01539 | 8.04136 | 0.0226 | 1.14885 | 1 | 1.14885 | 0 | 0 | True | 0 | 0 | 1.10036 | 0 | 51561 | 40040 | 51561 | 40040 |
| iter=0 | 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_failure | False | False | False | -20.0323 | 20.0597 | 0.0474934 | 0.57735 | 0.594221 | 0.343073 | 0 | 0 | True | 0 | 3.61407 | 0 | 2.89126 | 35 | 28 | 35 | 28 |
| iter=0 | 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_failure | False | False | False | -20.0323 | 20.0597 | 0.0474934 | 0.57735 | 0.594221 | 0.343073 | 0 | 0 | True | 0 | 3.61407 | 0 | 2.89126 | 35 | 28 | 35 | 28 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 1 | random_control | False | False | False | -4.32216 | 4.32471 | 0.00441011 | 0.577349 | 1 | 0.577349 | 0 | 0 | True | 0 | 0 | 0.720361 | 0 | 731 | 580 | 731 | 580 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 2 | random_control | False | False | False | -4.32216 | 4.32471 | 0.00441011 | 0.577349 | 1 | 0.577349 | 0 | 0 | True | 0 | 0 | 0.720361 | 0 | 731 | 580 | 731 | 580 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | True | True | False | -1.92896 | 1.93564 | 0.0132172 | 0.50582 | 1 | 0.50582 | 0 | 0 | True | 0 | 0 | 0 | 0 | -33565 | -30839 | -33565 | -30839 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 2 | random_control | True | True | False | -1.9271 | 1.93564 | 0.0132172 | 0.646038 | 1 | 0.646038 | 0 | 0 | True | 0 | 0 | 0 | 0 | -33565 | -30839 | -33565 | -30839 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | random_control | True | True | False | -0.806463 | 0.817711 | 0.0109381 | 1.02828 | 1 | 1.02828 | 0 | 0 | True | 0 | 0 | 0 | 0 | -24014 | -21737 | -24014 | -21737 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 1 | random_control | False | False | False | -5.79526 | 5.80114 | 0.0114662 | 0.512739 | 1 | 0.512739 | 0 | 0 | True | 0 | 0 | 0.794252 | 0 | 39745 | 29166 | 39745 | 29166 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 2 | random_control | False | False | False | -5.7938 | 5.80114 | 0.0114662 | 0.639634 | 1 | 0.639634 | 0 | 0 | True | 0 | 0 | 0.794252 | 0 | 39745 | 29166 | 39745 | 29166 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 1 | random_control | False | False | False | -13.7566 | 13.7675 | 0.0148415 | 0.735496 | 1 | 0.735496 | 0 | 0 | True | 0 | 0 | 1.91303 | 0 | 82348 | 68072 | 82348 | 68072 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 2 | random_control | False | False | False | -13.7615 | 13.7675 | 0.0148415 | 0.40315 | 1 | 0.40315 | 0 | 0 | True | 0 | 0 | 1.91303 | 0 | 82348 | 68072 | 82348 | 68072 |
| iter=0 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 2 | random_control | False | False | False | -8.81188 | 8.8334 | 0.0196158 | 1.09716 | 1 | 1.09716 | 0 | 0 | True | 0 | 0 | 1.21225 | 0 | 56097 | 44751 | 56097 | 44751 |
| iter=0 | 5 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | subset_failure | False | False | False | -26.3552 | 26.661 | 0.529796 | 0.57735 | 0.594937 | 0.343487 | 0 | 0 | True | 0 | 4.7548 | 0 | 3.80384 | 42 | 40 | 42 | 40 |
| iter=0 | 5 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_failure | False | False | False | -26.3552 | 26.661 | 0.529796 | 0.57735 | 0.594937 | 0.343487 | 0 | 0 | True | 0 | 4.7548 | 0 | 3.80384 | 42 | 40 | 42 | 40 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 1 | random_control | False | False | False | -4.07806 | 4.14988 | 0.124392 | 0.57735 | 1 | 0.57735 | 0 | 0 | True | 0 | 0 | 0.679677 | 0 | 675 | 560 | 675 | 560 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | base | 2 | random_control | False | False | False | -4.07806 | 4.14988 | 0.124392 | 0.57735 | 1 | 0.57735 | 0 | 0 | True | 0 | 0 | 0.679677 | 0 | 675 | 560 | 675 | 560 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | True | True | False | -1.79682 | 1.84682 | 0.0458187 | 1.09116 | 1 | 1.09116 | 0 | 0 | True | 0 | 0 | 0 | 0 | -27361 | -25396 | -27361 | -25396 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 2 | random_control | True | True | False | -0.0448734 | 0.0648784 | 0.0173248 | 1.1547 | 1 | 1.1547 | 0 | 0 | True | 0 | 0 | 0 | 0 | -56 | -315 | -56 | -315 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 0 | random_control | False | False | False | -6.23775 | 6.24149 | 0.0034009 | 1.1002 | 1 | 1.1002 | 0 | 0 | True | 0 | 0 | 0.856189 | 0 | 42868 | 31419 | 42868 | 31419 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 0 | random_control | False | False | False | -10.1664 | 10.1721 | 0.00509537 | 1.1149 | 1 | 1.1149 | 0 | 0 | True | 0 | 0 | 1.40868 | 0 | 61024 | 49777 | 61024 | 49777 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 0 | random_control | False | False | False | -7.37048 | 7.37108 | 0.00143955 | 0.416794 | 1 | 0.416794 | 0 | 0 | True | 0 | 0 | 1.00257 | 0 | 46781 | 36660 | 46781 | 36660 |
| iter=15 | 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 1 | random_control | False | False | False | -7.37004 | 7.37108 | 0.00143955 | 0.724179 | 1 | 0.724179 | 0 | 0 | True | 0 | 0 | 1.00257 | 0 | 46781 | 36660 | 46781 | 36660 |
| iter=15 | 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_failure | False | False | False | -2.34363 | 1127.8 | 1949.14 | 0.577412 | 0.5921 | 0.341886 | 0 | 0 | True | 0 | 0.630978 | 0 | 0 | 26 | 28 | 26 | 28 |
| iter=15 | 1 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 2 | subset_failure | False | False | False | -2.58603 | 1127.8 | 1949.14 | 0.577288 | 0.5921 | 0.341812 | 0 | 0 | True | 0 | 0.630978 | 0 | 0 | 26 | 28 | 26 | 28 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 0 | random_control | True | True | False | -1.86162 | 1.87992 | 0.0437604 | 0.418338 | 1 | 0.418338 | 0 | 0 | True | 0 | 0 | 0 | 0 | -28273 | -26335 | -28273 | -26335 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | True | True | False | -1.84829 | 1.87992 | 0.0437604 | 0.722896 | 1 | 0.722896 | 0 | 0 | True | 0 | 0 | 0 | 0 | -28273 | -26335 | -28273 | -26335 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | True | True | False | -0.0973327 | 0.111089 | 0.0122418 | 1.12367 | 1 | 1.12367 | 0 | 0 | True | 0 | 0 | 0 | 0 | -1727 | -1898 | -1727 | -1898 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 0 | random_control | False | False | False | -8.52561 | 8.52581 | 0.0116189 | 0.0176437 | 1 | 0.0176437 | 0 | 0 | True | 0 | 0 | 1.1676 | 0 | 56860 | 44299 | 56860 | 44299 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 1 | random_control | False | False | False | -8.5143 | 8.52581 | 0.0116189 | 0.991061 | 1 | 0.991061 | 0 | 0 | True | 0 | 0 | 1.1676 | 0 | 56860 | 44299 | 56860 | 44299 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 0 | random_control | False | False | False | -14.112 | 14.1213 | 0.0214787 | 0.436983 | 1 | 0.436983 | 0 | 0 | True | 0 | 0 | 1.95823 | 0 | 83830 | 70099 | 83830 | 70099 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 1 | random_control | False | False | False | -14.1062 | 14.1213 | 0.0214787 | 0.707134 | 1 | 0.707134 | 0 | 0 | True | 0 | 0 | 1.95823 | 0 | 83830 | 70099 | 83830 | 70099 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 0 | random_control | False | False | False | -8.08734 | 8.09111 | 0.00624528 | 0.602187 | 1 | 0.602187 | 0 | 0 | True | 0 | 0 | 1.10801 | 0 | 51699 | 40518 | 51699 | 40518 |
| iter=15 | 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 2 | random_control | False | False | False | -8.08766 | 8.09111 | 0.00624528 | 0.55215 | 1 | 0.55215 | 0 | 0 | True | 0 | 0 | 1.10801 | 0 | 51699 | 40518 | 51699 | 40518 |
| iter=15 | 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 0 | subset_failure | False | False | False | -3.49423 | 4.31827 | 1.42728 | 0.57735 | 0.594221 | 0.343074 | 0 | 0 | True | 0 | 0.940755 | 0 | 0 | 41 | 40 | 41 | 40 |
| iter=15 | 3 | subset_cardinality | subset_cardinality_bw12 | perm_seed1730 | 1 | subset_failure | False | False | False | -3.49423 | 4.31827 | 1.42728 | 0.57735 | 0.594221 | 0.343074 | 0 | 0 | True | 0 | 0.940755 | 0 | 0 | 41 | 40 | 41 | 40 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1730 | 1 | random_control | True | True | False | -1.93511 | 1.947 | 0.0106595 | 1.11509 | 1 | 1.11509 | 0 | 0 | True | 0 | 0 | 0 | 0 | -34933 | -32146 | -34933 | -32146 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 0 | random_control | True | True | False | -0.730541 | 0.731297 | 0.00421983 | 0.179114 | 1 | 0.179114 | 0 | 0 | True | 0 | 0 | 0 | 0 | -20960 | -18979 | -20960 | -18979 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | perm_seed1731 | 1 | random_control | True | True | False | -0.727506 | 0.731297 | 0.00421983 | 0.898336 | 1 | 0.898336 | 0 | 0 | True | 0 | 0 | 0 | 0 | -20960 | -18979 | -20960 | -18979 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 0 | random_control | False | False | False | -5.98331 | 5.99077 | 0.0135869 | 0.548875 | 1 | 0.548875 | 0 | 0 | True | 0 | 0 | 0.818296 | 0 | 40620 | 30347 | 40620 | 30347 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | base | 2 | random_control | False | False | False | -5.98254 | 5.99077 | 0.0135869 | 0.605364 | 1 | 0.605364 | 0 | 0 | True | 0 | 0 | 0.818296 | 0 | 40620 | 30347 | 40620 | 30347 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 0 | random_control | False | False | False | -13.7274 | 13.7314 | 0.0129766 | 0.311265 | 1 | 0.311265 | 0 | 0 | True | 0 | 0 | 1.91008 | 0 | 81733 | 68408 | 81733 | 68408 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1730 | 1 | random_control | False | False | False | -13.721 | 13.7314 | 0.0129766 | 0.807349 | 1 | 0.807349 | 0 | 0 | True | 0 | 0 | 1.91008 | 0 | 81733 | 68408 | 81733 | 68408 |
| iter=15 | 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | perm_seed1731 | 0 | random_control | False | False | False | -7.58856 | 7.60969 | 0.0182996 | 1.15458 | 1 | 1.15458 | 0 | 0 | True | 0 | 0 | 1.0374 | 0 | 47850 | 38437 | 47850 | 38437 |

## Group Sampling Audit

| group_id | group_role | rows | bases | variants | selected_iterations | selection_rate | base_instance_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v100_c360_seed1931 | control | 17 | 1 | 17 | 5 | 0.0416667 | random_3sat_control_v100_c360_seed1931 |
| random_3sat_control_v100_c425_seed1932 | control | 17 | 1 | 17 | 5 | 0.0416667 | random_3sat_control_v100_c425_seed1932 |
| random_3sat_control_v100_c600_seed1914 | control | 17 | 1 | 17 | 2 | 0.0166667 | random_3sat_control_v100_c600_seed1914 |
| random_3sat_control_v140_c595_seed1935 | control | 17 | 1 | 17 | 4 | 0.0333333 | random_3sat_control_v140_c595_seed1935 |
| random_3sat_control_v150_c525_seed1936 | control | 17 | 1 | 17 | 1 | 0.00833333 | random_3sat_control_v150_c525_seed1936 |
| random_3sat_control_v150_c638_seed1937 | control | 17 | 1 | 17 | 3 | 0.025 | random_3sat_control_v150_c638_seed1937 |
| random_3sat_control_v160_c704_seed2615 | control | 3 | 1 | 3 | 5 | 0.0416667 | random_3sat_control_v160_c704_seed2615 |
| random_3sat_control_v180_c760_seed3301 | control | 3 | 1 | 3 | 3 | 0.025 | random_3sat_control_v180_c760_seed3301 |
| random_3sat_control_v20_c85_seed1901 | control | 17 | 1 | 17 | 4 | 0.0333333 | random_3sat_control_v20_c85_seed1901 |
| random_3sat_control_v220_c928_seed3303 | control | 3 | 1 | 3 | 5 | 0.0416667 | random_3sat_control_v220_c928_seed3303 |
| random_3sat_control_v220_c942_seed3304 | control | 3 | 1 | 3 | 4 | 0.0333333 | random_3sat_control_v220_c942_seed3304 |
| random_3sat_control_v260_c1097_seed3305 | control | 3 | 1 | 3 | 7 | 0.0583333 | random_3sat_control_v260_c1097_seed3305 |
| random_3sat_control_v260_c1113_seed3306 | control | 3 | 1 | 3 | 3 | 0.025 | random_3sat_control_v260_c1113_seed3306 |
| random_3sat_control_v28_c119_seed1922 | control | 17 | 1 | 17 | 7 | 0.0583333 | random_3sat_control_v28_c119_seed1922 |
| random_3sat_control_v300_c1266_seed3307 | control | 3 | 1 | 3 | 3 | 0.025 | random_3sat_control_v300_c1266_seed3307 |
| random_3sat_control_v30_c128_seed1902 | control | 17 | 1 | 17 | 3 | 0.025 | random_3sat_control_v30_c128_seed1902 |
| random_3sat_control_v32_c136_seed1923 | control | 17 | 1 | 17 | 9 | 0.075 | random_3sat_control_v32_c136_seed1923 |
| random_3sat_control_v35_c149_seed1911 | control | 17 | 1 | 17 | 2 | 0.0166667 | random_3sat_control_v35_c149_seed1911 |
| random_3sat_control_v40_c170_seed1903 | control | 17 | 1 | 17 | 9 | 0.075 | random_3sat_control_v40_c170_seed1903 |
| random_3sat_control_v45_c191_seed1924 | control | 17 | 1 | 17 | 6 | 0.05 | random_3sat_control_v45_c191_seed1924 |
| random_3sat_control_v50_c213_seed1925 | control | 17 | 1 | 17 | 5 | 0.0416667 | random_3sat_control_v50_c213_seed1925 |
| random_3sat_control_v60_c180_seed1912 | control | 17 | 1 | 17 | 6 | 0.05 | random_3sat_control_v60_c180_seed1912 |
| random_3sat_control_v60_c255_seed1927 | control | 17 | 1 | 17 | 5 | 0.0416667 | random_3sat_control_v60_c255_seed1927 |
| random_3sat_control_v80_c260_seed1929 | control | 17 | 1 | 17 | 10 | 0.0833333 | random_3sat_control_v80_c260_seed1929 |
| random_3sat_control_v80_c340_seed1913 | control | 17 | 1 | 17 | 1 | 0.00833333 | random_3sat_control_v80_c340_seed1913 |
| random_3sat_control_v90_c383_seed1930 | control | 17 | 1 | 17 | 3 | 0.025 | random_3sat_control_v90_c383_seed1930 |
| formula_equiv_k10_php_p10 | priority | 20 | 2 | 17 | 73 | 0.608333 | k10_color9,php_p10_h9 |
| formula_equiv_k9_php_p9 | priority | 20 | 2 | 17 | 83 | 0.691667 | k9_color8,php_p9_h8 |
| subset_cardinality_bw12 | priority | 17 | 1 | 17 | 84 | 0.7 | subset_cardinality_bw12 |

## Pair Integrity

| group_id | present_in_train_manifest | rows | bases | variants | selected_iterations | selected_together_at_iteration_level | grpo_advantage_normalization_group | paired_variants_share_grpo_advantage_group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| formula_equiv_k9_php_p9 | True | 20 | 2 | 17 | 83 | True | cnf_id | False |
| formula_equiv_k10_php_p10 | True | 20 | 2 | 17 | 73 | True | cnf_id | False |
| subset_cardinality_bw12 | True | 17 | 1 | 17 | 84 | True | cnf_id | False |

## Interpretation

- Random controls do not receive final positive advantage in the proxy replay; positive raw/weighted cases are clamped to zero when the upper bound is active.
- Anchor rows do not receive raw or final positive advantage in this proxy replay. Since v1.4 still degraded wc1 anchors by iter=15, the missing exact training-batch solver_stats are material: the failure is not explained by the targeted acceptance proxy alone.
- Hard-negative recovery remains weak under the acceptance metric. Some hard-negative rows are search-positive relative to static weighted, which can be rewarded even when adapter-vs-cached acceptance is still mixed.
- The main actionable issue for v1.5 is not best checkpoint selection alone. Paired ranking and anchor preservation should become direct training constraints, and random/control positive raw advantages should be impossible by construction rather than only removed by a late upper-bound clamp.
