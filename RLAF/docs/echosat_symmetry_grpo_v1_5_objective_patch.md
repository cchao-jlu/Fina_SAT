# EchoSAT Symmetry GRPO v1.5 Objective Patch

This patch implements the next no-training step after the v1.4 reward replay audit.

## Goal

v1.5 keeps the training target on evidence-gated adapter-vs-cached search work. It does not optimize adapter-vs-plain protocol time and does not introduce a gate/selector.

The patch addresses the v1.4 failure mode where bad rows could still become positive GRPO samples inside their `cnf_id` normalization group:

- random/control rows cannot carry positive raw or final advantage;
- anchor failures cannot carry positive advantage;
- hard-negative failures cannot carry positive advantage;
- subset `subset_cardinality_bw12::perm_seed1730` remains positive-clamped;
- mixed pair/order groups are positive-clamped and receive an explicit pair-rank penalty;
- exact per-iteration reward replay is persisted for later audit.

## Code Changes

- `train_rlaf.py`
  - adds `symmetry_grpo_v1_5`;
  - adds `echosat_pair_rank_penalty`;
  - strengthens anchor and hard-negative failure penalties for v1.5;
  - adds `echosat_advantage_raw_upper_bound` so positive raw advantage can be clamped before weighting;
  - writes per-iteration replay CSVs when enabled.

- `configs/config_train_rlaf_echosat_symmetry_grpo_v1_5_wc1_pairstrict.yaml`
  - formal v1.5 config;
  - restarts from `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt`;
  - keeps wc1 low-warmup training;
  - persists replay under `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_5_WC1_PairStrict/reward_replay/`.

## Local Training Command

```bash
cd /home/sunshixin/chenchao/my_rlaf
/home/sunshixin/anaconda3/envs/rlaf/bin/python train_rlaf.py \
  --config-name config_train_rlaf_echosat_symmetry_grpo_v1_5_wc1_pairstrict
```

## Post-Training Checks

After training, inspect:

- `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_5_WC1_PairStrict/reward_replay/summary.csv`
- per-iteration `iter=000000_solver_stats.csv` replay files
- targeted acceptance on wc1, with wc3 as diagnostic

Acceptance remains search-work based:

- anchors `k9_color8`, `php_p9_h8` preserve wc1 search_ok;
- hard negatives `k10_color9`, `php_p10_h9` improve without pair/order inconsistency;
- random controls do not dominate positive wins;
- `subset_cardinality_bw12::perm_seed1730` stays negative;
- correctness stays matched for known expected labels;
- no solver speedup claim is implied.
