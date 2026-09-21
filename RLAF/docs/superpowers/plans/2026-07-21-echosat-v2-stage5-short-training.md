# EchoSAT v2 Stage 5 Short Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a 20-iteration EchoSAT v2 event-adapter shakeout from the conservative v1.2 checkpoint without losing the composed v2 model architecture or Stage 4 safety semantics.

**Architecture:** Formal v2 training builds the model from the current Hydra configuration, then loads compatible checkpoint tensors with the same strict core-coverage checks used by replay. A dedicated Stage 5 config enables optimizer, validation, checkpointing, and per-iteration reward artifacts while retaining weight-only orbit masking and the constrained v2 objective.

**Tech Stack:** Python 3.11, PyTorch, Hydra/OmegaConf, pytest, existing EchoSAT GRPO trainer.

---

### Task 1: Compatible Formal-Training Checkpoint Initialization

**Files:**
- Modify: `train_rlaf.py`
- Modify: `tests/test_echosat_v2_replay.py`

- [ ] Add failing tests for a non-replay v2 config with `training.echosat_compatible_checkpoint_init=true`.
- [ ] Assert the current config calls `init_transform(cfg)` and `init_model(cfg, transform)` before `load_compatible_checkpoint()`.
- [ ] Assert strict core checkpoint coverage remains mandatory and unrelated skipped tensors fail closed.
- [ ] Assert the compatible-init mode requires `from_checkpoint` and `echosat_target_mode=symmetry_grpo_v2`.
- [ ] Assert ordinary legacy non-replay configs still use `load_checkpoint()` unchanged.
- [ ] Run the focused tests and confirm RED.
- [ ] Implement the minimal compatible-init branch and generalized strict coverage helper.
- [ ] Run the focused and full v2 replay tests and confirm GREEN.

### Task 2: Stage 5 Configuration

**Files:**
- Create: `configs/config_train_rlaf_echosat_v2_stage5_short.yaml`
- Modify: `tests/test_echosat_v2_replay.py`

- [ ] Add a failing Hydra composition test.
- [ ] Create a config inheriting `config_train_rlaf_echosat_symmetry_grpo_v1_8_wc1_objectiverepair`.
- [ ] Set `echosat_target_mode=symmetry_grpo_v2`, `echosat_replay_only=false`, and `echosat_compatible_checkpoint_init=true`.
- [ ] Set 20 iterations, 48 CNFs per iteration, 48 optimizer steps, 16 samples, validation/checkpoint interval 5, and initial validation enabled.
- [ ] Retain the v1.2 `iter=15.pt` seed, weight-only residual adapter, orbit dimensions/masks, certification paths, and per-iteration reward replay.
- [ ] Use `runs/GNN_Glucose_3SAT_EchoSAT_v2_Stage5_Short` as the isolated output directory.
- [ ] Assert optimizer/scheduler and validation runtime remain enabled.
- [ ] Run config/lifecycle tests and confirm GREEN.

### Task 3: Reviews and Preflight

**Files:**
- Verify files from Tasks 1-2.

- [ ] Run the focused regression suite used for Stage 4 plus checkpoint-init tests.
- [ ] Complete specification review for current-config model construction, strict coverage, training lifecycle, and unchanged safety objective.
- [ ] Complete code-quality review for backward compatibility, malformed flags, skipped-key validation, and accidental replay-only behavior.
- [ ] Compose the Stage 5 config and load the real checkpoint without starting the training loop.
- [ ] Confirm trainable scope is exactly the six event-adapter tensors and the optimizer/scheduler are non-null.

### Task 4: Formal Short Training

**Files:**
- Generate: `runs/GNN_Glucose_3SAT_EchoSAT_v2_Stage5_Short/`

- [ ] Run the 20-iteration training command with `OMP_NUM_THREADS=1 KMP_USE_SHM=0`.
- [ ] Preserve stdout/stderr in `runs/GNN_Glucose_3SAT_EchoSAT_v2_Stage5_Short/train.log`.
- [ ] Monitor each validation/checkpoint boundary and stop on result mismatch, coverage loss, non-finite loss/gradient, missing reward artifacts, or safety-gate failure.
- [ ] Do not promote a checkpoint merely because its scalar metric improves.

### Task 5: Targeted Acceptance

**Files:**
- Analyze Stage 5 checkpoints and reward artifacts.

- [ ] Compare iteration 0, each saved checkpoint, `best.pt`, and the v1.2 seed on the existing targeted wc1 protocol.
- [ ] Require anchor search-ok preservation, no random-control positives, no plain-solved coverage loss, and non-positive known failure behavior.
- [ ] Report decisions/conflicts as primary outcomes and CPU only as a tie-breaker.
- [ ] Stop before Stage 6 runtime-gate work unless a checkpoint passes every earlier safety criterion.

## Repository Note

The `RLAF` workspace has no Git metadata, so commits are intentionally omitted.
