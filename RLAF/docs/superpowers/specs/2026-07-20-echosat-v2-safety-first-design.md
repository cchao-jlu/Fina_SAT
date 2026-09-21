# EchoSAT v2 Safety-First Orbit-Guided Solver Design

Date: 2026-07-20

## 1. Purpose

EchoSAT v2 must pursue two goals in a fixed priority order:

1. Preserve plain Glucose correctness and solved-instance coverage.
2. Produce auditable SAT-symmetry-specific search improvements.
3. Convert those improvements into end-to-end runtime gains where the available margin is large enough.

The design is fail-closed. Plain Glucose is the default execution path. Static weighting or event-adapter guidance is enabled only when the corresponding safety and evidence checks pass.

EchoSAT v2 is not a continuation of adding benchmark-specific exceptions to the v1.x reward. It replaces that pattern with explicit interfaces and constraints for:

- weighted-solver equivalence;
- orbit-conditioned inference;
- worst-variant training;
- runtime path selection;
- staged acceptance.

## 2. Current Baseline and Motivation

The current v1.2 calibrated protocol shows a small adapter-vs-cached final-solve improvement, but the complete protocol remains slower than plain Glucose. Adapter inference is approximately millisecond scale, while weighted-path setup and event collection dominate protocol overhead. Weighted variants also lose solved instances on high-risk families such as vertex-cover torus.

This means the model contains a potentially useful search signal, but the current system cannot safely expose it as a deployable speedup. The immediate problem is not adapter capacity. The immediate problems are:

- neutral weighted execution is not reliably equivalent to plain execution;
- orbit evidence affects training and audits more directly than inference;
- two-stage warmup/final execution pays duplicated solver costs;
- average rewards can hide permutation- or family-specific regressions;
- v1.x objectives have accumulated special-case rules that are difficult to generalize or audit.

## 3. Non-Goals

EchoSAT v2 will not initially:

- implement a complete dynamic symmetry solver;
- inject symmetry-image learned clauses;
- combine SBP preprocessing with the event adapter in the main experiment;
- optimize adapter activation rate;
- train a learned selector before a rule-based fail-closed gate is validated;
- claim solver speedup from final-solve CPU without protocol accounting;
- use random-control gains as symmetry-positive evidence.

## 4. System Architecture

The target architecture is:

```text
CNF
  -> Orbit Certification
  -> Static GNN
  -> Cheap Safety Preflight
  -> Short In-Process CDCL Probe
  -> Orbit-Aware Event Adapter
  -> Fail-Closed Path Gate
  -> Continue Plain or Inject Guidance
  -> Final Solver
```

Implementation is divided into two runtime milestones.

### 4.1 Milestone 1: Two-Stage Diagnostic Runtime

The existing warmup/final split may remain temporarily for model and objective validation. Results from this milestone may establish search-mechanism evidence but may not establish deployable speedup unless full protocol time improves.

### 4.2 Milestone 2: Single-Run Injection Runtime

The final runtime architecture uses one Glucose process:

```text
start plain Glucose
  -> run a bounded probe
  -> calculate event and gate features
  -> reject: continue unchanged
  -> accept: inject bounded weight residuals
  -> continue from the same solver state
```

The single-run milestone begins only after the no-event-cost oracle demonstrates enough final-solve gain to cover the measured minimum probe and injection cost.

## 5. Safety Invariants

The following invariants are mandatory and take precedence over average reward.

### 5.1 Correctness

- Known SAT/UNSAT results must match the expected result.
- A result mismatch is a hard failure, not a weighted penalty.
- UNKNOWN-labelled instances are excluded from correctness denominators but retained for runtime and search-work reporting.

### 5.2 Solved Coverage

- A plain-solved row must not become unsolved on an enabled guided path in the formal safety set.
- A path that loses any plain-solved base is rejected, regardless of gains on other bases.
- Timeout and near-cap outcomes are treated as safety failures during path qualification.

### 5.3 Neutral Weighted Equivalence

Before adapter training is promoted, the following paths must be behaviorally equivalent within defined tolerances:

```text
plain Glucose
neutral weighted Glucose
static weighted Glucose with neutral parameters
event adapter with zero delta
```

The audit must compare:

- result;
- solved coverage;
- preprocessing configuration;
- random seed handling;
- decisions and conflicts;
- final CPU and protocol time;
- variable and phase initialization;
- CPU-limit handling.

Neutral equivalence acceptance requires zero result/coverage differences and no systematic family-level search regression. Small timing noise is permitted, but any deterministic decisions/conflicts divergence must be attributed before proceeding.

Stage 1 uses two separate fail-closed gates rather than requiring time-limited
rows to have identical search counters:

1. **Deterministic search-equivalence gate.** Plain and neutral weighted
   Glucose run with identical preprocessing, seeds, and a deterministic
   conflict budget. Both binaries must implement the same inner-search budget
   check. Result, solved status, decisions, conflicts, propagations, and
   restarts must match exactly on every pair.
2. **CPU-limit coverage gate.** Plain and neutral weighted Glucose run with
   the same CPU limit and protocol settings. Result and solved coverage must
   match, and a plain-solved row may not become neutral-unsolved. Decisions and
   conflicts on CPU-limited `INDETERMINATE` rows are diagnostic because their
   stopping point is clock-driven rather than deterministic.

The two gates must be reported separately. Passing the deterministic gate
cannot hide CPU-limit coverage loss, and passing the CPU gate cannot excuse a
deterministic trajectory difference. The formal evidence must record solver
binary hashes, input hashes, argv, budget type/value, and whether an external
timeout occurred.

### 5.4 Fail-Closed Execution

- Missing orbit evidence selects plain execution.
- Missing event evidence selects plain execution.
- Missing or invalid gate features select plain execution.
- Out-of-distribution feature values select plain execution.
- Weighted-path risk above threshold selects plain execution.
- The initial formal adapter activation target is at most 15 percent of bases.

## 6. Orbit Certification Interface

Orbit certification remains offline and auditable. Each variable-level record must expose:

| Field | Meaning |
| --- | --- |
| `base_instance_id` | Aggregation and split unit |
| `variant` | Base or permutation variant |
| `variable_id` | Variable in the current variant |
| `orbit_id` | Certified orbit identifier |
| `orbit_size` | Number of variables in the orbit |
| `structure_type` | PHP, coloring, row-column, torus, graph automorphism, or unknown |
| `orbit_confidence` | Confidence in `[0, 1]` |
| `valid_for_training` | Eligible for symmetry-positive training |
| `needs_refinement` | Certification disagreement or ambiguity |

Random controls must have zero orbit confidence and no valid training orbit. Weak or pseudo orbits may be used for diagnostics and negative-boundary training but cannot receive the full strong-symmetry weight.

The model input should use compact orbit features, not raw string identifiers. Required variable-level inputs are:

```text
valid_orbit_mask
orbit_confidence
log1p(orbit_size)
structure_type_embedding
```

## 7. Orbit-Relative Event Representation

Raw event counts are insufficient because they depend on formula scale, warmup length, and solver trajectory. EchoSAT v2 adds orbit-relative features computed only within certified valid orbits.

For each raw event channel, calculate:

```text
within_orbit_rank
within_orbit_zscore
within_orbit_share
orbit_channel_variance
orbit_nonzero_coverage
```

Core event channels remain:

- decisions;
- propagations;
- conflict-literal participation;
- learnt-literal participation;
- activity;
- positive/negative polarity statistics where available.

Graph-level evidence features include:

```text
valid_orbit_count
valid_orbit_variable_fraction
mean_orbit_confidence
event_active_orbit_fraction
mean_orbit_event_variance
warmup_conflict_rate
warmup_propagation_rate
```

If an orbit has no meaningful event variance, its adapter delta must be zero. The model is not allowed to manufacture within-orbit identity without event evidence.

## 8. Orbit-Aware Adapter

The adapter predicts a bounded residual over the frozen static GNN output:

```text
delta_weight_i = Adapter(
    base_embedding_i,
    static_output_i,
    raw_event_i,
    orbit_relative_event_i,
    orbit_features_i,
    graph_risk_features
)
```

The first formal v2 model is weight-only:

```text
adapted_weight_i = static_weight_i + delta_weight_i
adapted_phase_i = static_phase_i
```

Phase residuals remain disabled until weight-only guidance passes all safety and permutation acceptance gates. When later enabled, phase uses a separate head and a stricter evidence threshold.

The adapter applies hard masks after prediction:

```text
delta_weight_i = 0 if not valid_orbit_mask_i
delta_weight_i = 0 if orbit_event_variance_i < event_variance_threshold
delta_weight_i = 0 if graph_weighted_risk > risk_threshold
delta_weight_i = clip(delta_weight_i, -delta_max, delta_max)
```

The architecture must not depend on arbitrary orbit labels. Renaming variables and consistently renaming orbit membership must preserve aligned predictions up to solver-event variation.

## 9. Training Objective

EchoSAT v2 replaces benchmark-specific reward accumulation with four primary objective components.

### 9.1 Search Improvement

Positive search reward is available only when both decisions and conflicts improve relative to the cached/static baseline:

```text
search_positive =
    decisions_adapter < decisions_cached - eps_decisions
    and conflicts_adapter < conflicts_cached - eps_conflicts
```

CPU improvement is a bounded tie-breaker, not an independent source of positive reward.

### 9.2 Worst-Variant Consistency

Training and validation group rows by `base_instance_id`. For each base, use the worst valid variant when calculating the positive objective:

```text
base_search_score = min(search_score_base, search_score_perm_1, search_score_perm_2, ...)
```

An average positive score cannot compensate for a strongly negative permutation. Event alignment quality may downweight consistency regularization, but it may not remove the worst-variant safety test.

### 9.3 Plain-Safety Constraint

The following cases receive hard non-positive advantage:

- plain solved and guided path unsolved;
- result mismatch;
- weighted-risk blocked;
- near cap;
- random control;
- missing valid orbit evidence;
- search blowup in either decisions or conflicts.

Blocked rows must be removed from positive group normalization before group mean and variance are calculated. Post-normalization clamping alone is insufficient because blocked rows can still alter other rows' advantages.

### 9.4 Outside-Orbit Delta Regularization

The adapter is penalized for modifying variables outside valid evidence:

```text
L_outside = mean(abs(delta_weight_i) * (1 - valid_orbit_mask_i))
```

Within valid orbits, delta magnitude is also regularized when event variance or orbit confidence is weak.

### 9.5 Combined Objective

The formal objective is:

```text
L_total =
    L_search
  + lambda_worst * L_worst_variant
  + lambda_safe * L_plain_safety
  + lambda_outside * L_outside
  + lambda_magnitude * L_delta_magnitude
```

`L_plain_safety` is implemented as a hard advantage block plus a large training penalty. It is not traded against positive runtime reward.

## 10. Runtime Gate

The initial gate is deterministic and rule-based. It may use only information available before the final path decision:

- orbit certification summary;
- static GNN statistics;
- formula metadata;
- bounded warmup statistics;
- orbit-relative event evidence;
- a separately validated weighted-path risk score.

It may not use full adapter final runtime, oracle sample selection, expected answer, or per-instance calibration from the evaluation set.

The gate outputs:

```text
PLAIN
STATIC_WEIGHTED
EVENT_ADAPTER
```

Initial policy:

```text
if neutral equivalence is not certified:
    PLAIN
elif weighted risk is high or out of distribution:
    PLAIN
elif valid orbit evidence is missing:
    PLAIN
elif event evidence is weak:
    PLAIN or STATIC_WEIGHTED
elif all adapter eligibility checks pass:
    EVENT_ADAPTER
else:
    PLAIN
```

A learned gate is permitted only after the rule-based gate produces a nonzero safe gain on held-out bases without losing plain-solved coverage.

## 11. Evaluation Protocol

### 11.1 Fixed Methods

Formal evaluation reports:

1. plain Glucose;
2. neutral weighted Glucose;
3. static weighted Glucose;
4. cached trace without adapter;
5. orbit-aware event adapter;
6. fail-closed rule gate;
7. matched random weight perturbation;
8. optional static symmetry-breaking baseline.

### 11.2 Aggregation

The primary unit is `base_instance_id`. Permutation variants and repeats are paired observations under the same base, not independent successes.

Required splits are:

- base-heldout;
- generator-seed-heldout;
- family-heldout;
- random non-symmetric controls;
- weighted-path stress families.

### 11.3 Lexicographic Acceptance

A checkpoint or runtime policy is accepted only in this order:

1. zero known-result mismatches;
2. zero lost plain-solved bases on the formal safety set;
3. no base with more than 5 percent decisions or conflicts regression in its worst evaluated variant;
4. family-level 90th percentile protocol regression no greater than 2 percent;
5. positive base-level search-work improvement relative to cached/static;
6. positive end-to-end protocol improvement relative to plain.

Failure at an earlier item prevents promotion based on a later item.

### 11.4 Claim Levels

Results are classified as:

| Level | Required Evidence |
| --- | --- |
| Mechanism evidence | Valid-orbit search improvements stable across permutations |
| Runtime viability | Full protocol does not materially regress and selected bases improve |
| Symmetry-specific benefit | Matched perturbations and random controls cannot explain the improvement |
| Solver speedup | Held-out base-level end-to-end improvement with safety invariants satisfied |

## 12. Staged Execution Plan

### Stage 0: Freeze Reference Artifacts

- Preserve v1.2 `iter=15.pt` as the conservative reference checkpoint.
- Freeze current canonical manifests, safety bases, controls, and stress families.
- Do not select thresholds on the final held-out set.

Exit condition: reference hashes and evaluation manifests are recorded.

### Stage 1: Neutral Weighted Equivalence

- Add equivalence tests for plain, neutral, zero-static, and zero-delta paths.
- Attribute every deterministic search difference.
- Repair weighted solver initialization or preprocessing until coverage is equal.
- Align plain and weighted inner-search budget checks and expose the same
  deterministic conflict-budget CLI on both binaries.
- Run and report the deterministic search-equivalence gate separately from the
  CPU-limit coverage gate.

Exit condition: every deterministic pair matches exactly, the CPU-limit gate
has zero result/coverage loss, and neither gate contains missing or externally
timed-out formal rows.

### Stage 2: Weight-Only Safety Baseline

- Disable adapter phase changes.
- Apply conservative delta clipping.
- Re-run canonical and stress acceptance.

Exit condition: no lost plain-solved bases and worst-variant regression within tolerance.

### Stage 3: Orbit-Aware Features

- Attach certified orbit features to model graphs.
- Calculate orbit-relative event channels.
- Add inference-time hard masks.
- Audit permutation alignment before training.

Exit condition: renamed inputs produce aligned orbit-relative features and aligned zero/event-controlled deltas.

### Stage 4: Constrained Objective

- Implement blocked-row pre-normalization exclusion.
- Add worst-variant objective.
- Add plain-safety and outside-orbit constraints.
- Run a short formal-path reward replay before training.

Exit condition: all blocked classes have non-positive training-visible advantage and valid positives remain nonzero.

### Stage 5: Short Training and Targeted Acceptance

- Initialize from the conservative v1.2 checkpoint.
- Run a short training budget.
- Compare against v1.2 using the lexicographic gate.

Exit condition: the new checkpoint beats or matches v1.2 at every earlier safety criterion and improves search work on held-out symmetric bases.

### Stage 6: Fail-Closed Runtime Gate

- Calibrate a deterministic gate on train/dev bases.
- Limit formal adapter activation to at most 15 percent initially.
- Evaluate activation precision, rejected positives, and avoided regressions.

Exit condition: zero coverage loss and positive protocol delta on selected held-out bases.

### Stage 7: No-Event-Cost Oracle

- Measure final-solve gain plus actual adapter inference cost.
- Compare that gain with the minimum effective warmup cost.

Exit condition: expected selected-path gain exceeds probe and injection cost with a safety margin.

### Stage 8: Single-Run Injection

- Add a bounded in-process event probe.
- Inject weight residuals without restarting the solver.
- Retain an immediate plain fallback when the gate rejects guidance.

Exit condition: full held-out protocol satisfies the solver-speedup claim level.

## 13. Required Tests

The implementation must include focused tests for:

- neutral weighted DIMACS equivalence;
- zero-delta adapter equivalence;
- orbit feature attachment and batching;
- orbit-relative ranks, shares, and variance;
- random controls receiving no valid orbit mask;
- delta being zero outside valid orbits;
- delta being zero under weak event evidence;
- permutation alignment of orbit-relative features;
- blocked rows excluded before GRPO normalization;
- worst-variant loss selecting the minimum variant score;
- gate fail-closed behavior for missing and out-of-distribution features;
- plain-solved coverage rejection;
- single-run injection preserving solver state and result.

## 14. Observability and Artifacts

Every formal run must save:

- exact checkpoint and configuration hash;
- manifest and orbit-certification hash;
- per-row solver results;
- per-base and per-family summaries;
- gate decision and rejection reason;
- weighted-risk score;
- orbit and event evidence summaries;
- decisions/conflicts/final CPU/protocol time;
- adapter delta magnitude and activation fraction;
- worst-variant acceptance status;
- correctness and plain-solved coverage status.

The gate rejection reason uses a fixed enum so failures remain auditable:

```text
NO_VALID_ORBIT
WEAK_EVENT_EVIDENCE
WEIGHTED_PATH_RISK
OUT_OF_DISTRIBUTION
NEAR_CAP
MISSING_FEATURES
STATIC_ONLY
ADAPTER_ALLOWED
```

## 15. Promotion and Stop Rules

Promote an experiment only when it passes the complete lexicographic acceptance sequence. Do not promote based on a scalar score alone.

Stop or redirect the branch when any of the following persists after targeted diagnosis:

- neutral weighted execution cannot preserve plain coverage;
- orbit-aware features do not improve permutation stability;
- valid symmetric bases do not show final-search gains under no-event-cost accounting;
- the rule gate must reject nearly every base to remain safe;
- selected-path final gains remain smaller than the minimum effective probe cost.

If neutral weighted equivalence cannot be repaired, the next branch should inject bounded refocus information directly into unmodified plain solver semantics rather than continuing the current weighted input path.

## 16. Recommended Immediate Scope

The first implementation plan should cover only Stages 0 through 4:

1. freeze reference artifacts;
2. neutral weighted equivalence audit;
3. weight-only safety baseline;
4. orbit-aware feature representation;
5. constrained reward replay.

Training a new checkpoint, building a runtime selector, and modifying the Glucose kernel are deliberately excluded from the first implementation scope. They depend on the earlier safety and mechanism gates.
