# EchoSAT v2 Variant-Level Eligibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace base-wide stochastic one-vote eligibility with fail-closed variant-level eligibility while retaining base worst-variant recovery pressure.

**Architecture:** `build_symmetry_grpo_v2_target()` will separate hard safety blockers from dual-search qualification, aggregate hard safety and mean search score by `(base_instance_id, variant)`, and combine those variant facts with row-level dual improvement. Base-level `worst_variant_score` remains unchanged as an objective and diagnostic term. The offline replay audit will add variant/base attribution without changing the three mandatory acceptance checks.

**Tech Stack:** Python 3.11, pandas, NumPy, unittest/pytest, existing EchoSAT replay CLI.

---

### Task 1: Define Variant-Level Eligibility With Failing Tests

**Files:**
- Modify: `tests/test_echosat_v2_objective.py`

- [ ] **Step 1: Add a test proving stochastic failures do not cross variants**

Add a test using two variants under one base. Give the safe variant two dual-improving rows. Give the second variant one improving row and one regressing row, producing a non-positive variant mean without a hard safety failure. Assert that the safe variant rows are eligible, the non-positive variant rows are ineligible, and all rows share the same negative `worst_variant_score`.

```python
def test_variant_eligibility_does_not_broadcast_stochastic_failure_across_base(self):
    guided = pd.DataFrame([
        _guided_row(1, sample_id=0, base_instance_id="shared", variant="safe"),
        _guided_row(1, sample_id=1, base_instance_id="shared", variant="safe", decisions=75.0, conflicts=65.0),
        _guided_row(2, sample_id=0, base_instance_id="shared", variant="mixed"),
        _guided_row(2, sample_id=1, base_instance_id="shared", variant="mixed", decisions=180.0, conflicts=180.0),
    ])
    plain = pd.DataFrame([
        _plain_row(1, sample_id=0), _plain_row(1, sample_id=1),
        _plain_row(2, sample_id=0), _plain_row(2, sample_id=1),
    ])
    static = pd.DataFrame([
        _static_row(1, sample_id=0), _static_row(1, sample_id=1),
        _static_row(2, sample_id=0), _static_row(2, sample_id=1),
    ])

    result = build_symmetry_grpo_v2_target(guided, plain, static, cpu_cap=10.0)

    assert result.loc[result["variant"].eq("safe"), "v2_positive_eligible"].all()
    assert not result.loc[result["variant"].eq("mixed"), "v2_positive_eligible"].any()
    assert result["worst_variant_score"].lt(0.0).all()
```

- [ ] **Step 2: Add a test proving a hard failure blocks its whole variant only**

Create a safe variant and a risk variant under one base. Set `echosat_weighted_risk=1.0` on one risk-variant row. Assert `v2_variant_hard_blocked=True` for both risk rows, false for safe rows, and safe dual-improving rows remain eligible.

- [ ] **Step 3: Add validation and order-invariance tests**

Add assertions that empty/null `base_instance_id` or `variant` raises `ValueError`, non-finite `search_score` cannot make a variant positive-capable, and shuffling rows preserves eligibility when keyed by `(cnf_id, sample_id)`.

- [ ] **Step 4: Run the new tests and verify RED**

Run:

```bash
OMP_NUM_THREADS=1 KMP_USE_SHM=0 .venv/bin/python -m pytest -q \
  tests/test_echosat_v2_objective.py -k 'variant_eligibility or hard_failure_blocks'
```

Expected: failures showing the current base-wide `v2_positive_eligible` broadcast and missing variant diagnostic columns.

### Task 2: Implement Three-Layer Objective Semantics

**Files:**
- Modify: `src/echosat/objective_v2.py`
- Test: `tests/test_echosat_v2_objective.py`

- [ ] **Step 1: Separate hard safety from search qualification**

Keep result, baseline, control, near-cap, weighted-risk, orbit-evidence, guided-metric, and missing-data conditions in `hard_safety_blocked`. Keep strict decisions/conflicts improvement in `row_positive_candidate`:

```python
hard_safety_blocked = (
    control
    | plain_result_mismatch
    | static_result_mismatch
    | plain_solved_guided_unsolved
    | static_solved_guided_unsolved
    | plain_unsolved
    | static_unsolved
    | near_cap
    | weighted_risk
    | (~valid_evidence)
    | (~valid_guided)
    | missing_plain
    | missing_static
    | invalid_static
)
row_positive_candidate = (
    (~hard_safety_blocked)
    & dual_improvement
    & (~static_search_blowup)
)
```

- [ ] **Step 2: Aggregate variant facts without changing row order**

Validate nonempty grouping keys, construct a temporary frame indexed like `out`, and use group transforms:

```python
variant_group = [out["base_instance_id"].astype(str), out["variant"].astype(str)]
variant_hard_blocked = pd.Series(hard_safety_blocked, index=out.index).groupby(
    variant_group, sort=False
).transform("any").to_numpy(dtype=bool)
variant_mean_search_score = pd.Series(search_score, index=out.index).groupby(
    variant_group, sort=False
).transform("mean").to_numpy(dtype=np.float64)
variant_positive_capable = (
    (~variant_hard_blocked)
    & np.isfinite(variant_mean_search_score)
    & (variant_mean_search_score > 0.0)
)
positive_eligible = row_positive_candidate & variant_positive_capable
```

- [ ] **Step 3: Preserve base worst-variant pressure**

Continue using `worst_variant_scores(out, "search_score")` for base-level diagnostics and recovery pressure. Use row-level `search_score` for `v2_objective_search_score` so eligible samples retain within-CNF variance. Replace the base-wide minimum blocked penalty with a variant-wide minimum penalty, and add `worst_variant_penalty` only to truly ineligible rows.

```python
row_blocked = ~positive_eligible
blocked_penalty = np.maximum(blocked_penalty, row_blocked.astype(np.float64))
blocked_penalty += worst_variant_penalty * row_blocked.astype(np.float64)
out["echosat_cost"] = np.nan_to_num(
    -out["search_score"].to_numpy(dtype=np.float64)
    + blocked_penalty,
    nan=1.0,
    posinf=1.0,
    neginf=1.0,
)
```

Do not broadcast `worst_variant_score` as the eligible ranking target: that produces constant cost within each CNF and zero GRPO variance. Do not add `worst_variant_penalty` to eligible rows.

- [ ] **Step 4: Expose stable diagnostics**

Write strict boolean/numeric columns:

```python
out["v2_hard_safety_blocked"] = hard_safety_blocked
out["v2_row_positive_candidate"] = row_positive_candidate
out["v2_variant_hard_blocked"] = variant_hard_blocked
out["v2_variant_mean_search_score"] = variant_mean_search_score
out["v2_variant_positive_capable"] = variant_positive_capable
out["v2_base_blocked"] = variant_hard_blocked
out["v2_positive_eligible"] = positive_eligible
```

`v2_base_blocked` remains as a compatibility alias for the narrower variant blocker during this stage; tests must document that semantic change.

- [ ] **Step 5: Run objective tests and verify GREEN**

Run:

```bash
OMP_NUM_THREADS=1 KMP_USE_SHM=0 .venv/bin/python -m pytest -q tests/test_echosat_v2_objective.py
```

Expected: all objective tests pass, including the new variant tests.

### Task 3: Add Replay Attribution Without Relaxing Acceptance

**Files:**
- Modify: `replay_echosat_v2_objective.py`
- Modify: `tests/test_echosat_v2_replay.py`

- [ ] **Step 1: Add failing audit-summary tests**

Construct rows spanning two bases and three variants. Assert the generated document reports:

```text
eligible variants
hard-blocked variants
per-base eligible rows
per-base eligible variants
per-base worst variant score
hard-safety rejection counts
```

Keep `CHECK_NAMES` and the mandatory exit-code semantics unchanged.

- [ ] **Step 2: Run replay tests and verify RED**

Run:

```bash
OMP_NUM_THREADS=1 KMP_USE_SHM=0 .venv/bin/python -m pytest -q \
  tests/test_echosat_v2_replay.py -k 'variant or attribution or audit_doc'
```

Expected: failures because the document currently reports only row counts and three checks.

- [ ] **Step 3: Build fail-closed attribution helpers**

Add a helper that accepts the replay frame and returns deterministic summary lines/tables. Treat missing diagnostic columns as zero eligible and report the missing columns; do not infer eligibility from numeric truthiness. Use strict boolean checks matching `_strict_eligibility()`.

- [ ] **Step 4: Extend the Markdown audit artifact**

Append compact `Variant Summary`, `Base Summary`, and `Hard-Safety Rejections` sections. Sort base IDs and variants lexicographically for deterministic regeneration. Do not add new acceptance checks in this task.

- [ ] **Step 5: Run replay tests and verify GREEN**

Run:

```bash
OMP_NUM_THREADS=1 KMP_USE_SHM=0 .venv/bin/python -m pytest -q tests/test_echosat_v2_replay.py
```

Expected: all replay tests pass.

### Task 4: Regression, Reviews, and Formal Replay

**Files:**
- Regenerate: `runs/analysis/echosat_v2_stage4_reward_replay/iter=000000_solver_stats.csv`
- Regenerate: `runs/analysis/echosat_v2_stage4_reward_replay/summary.csv`
- Regenerate: `runs/analysis/echosat_v2_stage4_reward_replay/checks.csv`
- Regenerate: `runs/analysis/echosat_v2_stage4_reward_replay/train.log`
- Regenerate: `docs/echosat_v2_stage4_reward_replay.md`

- [ ] **Step 1: Run the focused regression suite**

```bash
OMP_NUM_THREADS=1 KMP_USE_SHM=0 .venv/bin/python -m pytest -q \
  tests/test_echosat_v2_replay.py \
  tests/test_echosat_v2_objective.py \
  tests/test_dimacs_dataset_paths.py \
  tests/test_echosat_symmetry_grpo_v1_8_train_target.py \
  tests/test_echosat_symmetry_grpo_v1_8_reward_replay.py
```

Expected: zero failures.

- [ ] **Step 2: Complete specification review**

Verify line by line against `docs/superpowers/specs/2026-07-21-echosat-v2-variant-level-eligibility-design.md`. Do not proceed when row hard-safety, variant hard blocking, positive-mean qualification, base worst pressure, or strict boolean eligibility is missing.

- [ ] **Step 3: Complete code-quality review**

Review grouping-key validation, index/order preservation, finite-value handling, compatibility columns, vectorized performance, and deterministic diagnostics. Do not proceed on Important or Critical findings.

- [ ] **Step 4: Run formal replay**

```bash
PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 KMP_USE_SHM=0 \
.venv/bin/python train_rlaf.py \
  --config-name config_train_rlaf_echosat_v2_stage4_replay \
  > runs/analysis/echosat_v2_stage4_reward_replay/train.log 2>&1
```

Expected: replay-only exit code 0, 1,184 rows, 74 CNFs, 16 samples per CNF, and no optimizer/checkpoint activity.

- [ ] **Step 5: Run acceptance CLI**

```bash
.venv/bin/python replay_echosat_v2_objective.py \
  --rows runs/analysis/echosat_v2_stage4_reward_replay/iter=000000_solver_stats.csv \
  --checks runs/analysis/echosat_v2_stage4_reward_replay/checks.csv \
  --doc docs/echosat_v2_stage4_reward_replay.md
```

Expected mandatory checks:

```text
blocked_rows_non_positive=True
eligible_positive_exists=True
all_v2_stage4_checks=True
```

Diagnostic expectation from the pre-change replay is approximately 123 eligible rows across 10 positive-capable variants, with zero random-control eligible rows. Treat deviations as evidence to analyze, not values to force.

### Task 5: Final Verification

**Files:**
- Verify all files listed above.

- [ ] **Step 1: Run syntax checks**

```bash
.venv/bin/python -m py_compile \
  src/echosat/objective_v2.py \
  replay_echosat_v2_objective.py \
  tests/test_echosat_v2_objective.py \
  tests/test_echosat_v2_replay.py
```

Expected: exit code 0 with no output.

- [ ] **Step 2: Verify replay invariants from the generated CSV**

Confirm strict booleans, blocked positive count 0, eligible positive count greater than 0, random-control eligible count 0, and deterministic per-base/per-variant summaries.

- [ ] **Step 3: Stop before training**

Report the Stage 4 result. Do not launch formal training without a separate user approval.

## Repository Note

This workspace snapshot has no Git metadata in `RLAF`, so commit steps are intentionally omitted. File changes and verification artifacts provide the review boundary.
