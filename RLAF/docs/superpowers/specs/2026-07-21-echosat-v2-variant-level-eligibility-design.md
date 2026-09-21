# EchoSAT v2 Variant-Level Positive Eligibility Design

Date: 2026-07-21

## 1. Context

The Stage 4 formal replay produced 1,184 rows for 74 CNFs. Orbit metadata and event evidence are now wired correctly: 912 rows have valid certified orbit evidence and nonzero symmetry evidence. The replay still produced zero positive-eligible rows because the current objective broadcasts any row-level failure across the entire `base_instance_id`.

Each base contains multiple permutation variants and each variant contains 16 stochastic samples. The current `groupby(base_instance_id).transform("any")` therefore treats one failed stochastic sample as proof that every sample from every variant is unsafe. This removes all positive learning signal even though 223 rows satisfy the strict row-level safety and dual-search criteria.

The objective must preserve the safety-first policy without confusing stochastic row failures with base-wide invalidity.

## 2. Decision

Positive eligibility moves from base-level one-vote veto to a three-layer constraint:

1. **Row hard-safety gate.** A row is blocked when it is a control, has missing or invalid baselines, has a result/coverage failure, is near the CPU cap, has weighted-path risk, lacks certified symmetry evidence, has invalid guided metrics, or fails the strict decisions-and-conflicts dual-improvement condition.
2. **Variant safety gate.** A variant is positive-capable only when none of its rows has a hard safety failure and its mean `search_score` is strictly positive.
3. **Base worst-variant pressure.** The minimum mean variant score remains broadcast to the base as `worst_variant_score` and strengthens blocked-row recovery pressure. Eligible rows retain their row-level `search_score` as the GRPO ranking target so the base-level constant cannot erase within-CNF variance or positive learning signal.

This design keeps hard-risk variants non-positive while allowing safe variants from the same base to provide learning signal.

## 3. Eligibility Semantics

For each row, define:

```text
hard_safety_blocked =
  control
  or missing/invalid/unsolved baseline
  or result mismatch
  or plain/static solved but guided unsolved
  or near-cap
  or weighted-path risk
  or invalid orbit evidence
  or invalid guided metrics

dual_improvement =
  guided decisions < static decisions
  and guided conflicts < static conflicts

row_positive_candidate =
  not hard_safety_blocked
  and dual_improvement
  and not static_search_blowup
```

For each `(base_instance_id, variant)` group:

```text
variant_hard_blocked = any(hard_safety_blocked)
variant_mean_search_score = mean(search_score)
variant_positive_capable =
  not variant_hard_blocked
  and variant_mean_search_score > 0
```

Final eligibility is:

```text
v2_positive_eligible =
  row_positive_candidate
  and variant_positive_capable
```

Eligibility values remain strict booleans. Missing, malformed, or non-finite inputs fail closed.

## 4. Penalty Semantics

- Blocked rows retain non-positive final advantage.
- Hard-safety failures retain their existing row penalties.
- A hard-blocked variant applies a minimum penalty to every row in that variant, not to unrelated variants in the same base.
- `worst_variant_score` and `worst_variant_penalty` remain base-level diagnostics.
- `v2_objective_search_score` is the row-level `search_score`; eligible cost is therefore `-search_score` and preserves within-CNF ranking.
- A negative worst variant increases the penalty of ineligible rows from that base, but does not enter eligible normalization or suppress positive samples from a safe sibling variant.
- Random controls remain permanently ineligible for positive advantage.

## 5. Replay Acceptance

The existing mandatory checks remain:

- every blocked row has non-positive `grpo_final_advantage`;
- at least one eligible row has positive `grpo_final_advantage`;
- eligibility values are valid booleans.

The replay report must additionally expose:

- eligible row count;
- positive-eligible variant count;
- hard-blocked variant count;
- per-base worst variant score;
- per-base eligible rows and eligible variants;
- rejection counts by hard-safety reason.

No training starts unless all mandatory checks pass.

## 6. Expected Evidence From Current Replay

Applying the approved semantics diagnostically to the current replay yields:

- current base-any eligibility: 0 rows;
- strict row-level candidates: 223 rows;
- variant-level eligible rows: 123 rows;
- positive-capable variants: 10;
- random-control eligible rows: 0.

These values are diagnostic expectations for regression tests and replay review, not fixed production thresholds.

## 7. Tests

Tests must prove:

- one bad stochastic row does not block a different safe variant;
- one hard-safety row blocks its entire variant;
- a non-positive variant mean blocks that variant even when one row improves;
- a safe positive-mean variant retains only its dual-improving rows;
- a negative variant still determines the base worst-variant score and penalty;
- random controls never become positive-eligible;
- blocked rows remain non-positive after GRPO normalization;
- malformed grouping keys and non-finite scores fail closed;
- row order does not change variant eligibility or worst-variant results.

## 8. Scope

This change is limited to the v2 constrained objective, focused tests, replay diagnostics, and the Stage 4 replay artifact. It does not start training, change the adapter architecture, relax weighted-risk thresholds, or alter solver execution.
