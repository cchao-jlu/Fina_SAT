# Symmetry Adapter Objective Fix v1

## Scope

Objective Fix v1 is a training-objective repair, not a runtime claim. It must not
train a gate/selector, must not expand the full runtime benchmark, and must not
use wall-clock as the primary reward.

The goal is:

> Allow adapter guidance changes only when symmetry-valid event-orbit evidence
> exists; suppress adapter perturbation for non-symmetric, no-valid-orbit, or
> permutation-inconsistent cases.

## Primary Target

The primary proxy target is final search-count direction:

- reduce `final_decisions` delta versus the adapter baseline comparison;
- reduce `final_conflicts` delta versus the adapter baseline comparison;
- treat wall-clock only as a later diagnostic, not as the objective reward.

For v1 offline proxy, deltas are read from the frozen v2 runtime snapshot. Negative
decision/conflict deltas are rewarded; positive deltas are penalized.

## Hard Constraints

- Correctness must not degrade.
- If plain/static/cached baseline solves an instance, adapter final must not turn it
  into a loss.
- Non-symmetric control changes must not be counted as symmetry benefit.
- Full runtime expansion is out of scope until targeted mechanism re-audit improves.

## Symmetry Condition

Adapter separation is a positive signal only when all of the following hold:

- `event_row_valid=True`;
- the orbit is non-singleton and passes refined orbit validity;
- static orbit collapse holds under the configured threshold;
- event identity is positive on that valid row.

Invalid rows such as `static_mu_not_collapsed`, singleton rows, and below-min-size
rows can be reported for diagnosis, but they must not be used as positive identity
training evidence.

## Negative Condition

The adapter delta should be close to zero when:

- the family is a non-symmetric control;
- no valid event orbit exists;
- no activity or no event evidence is present;
- the only apparent identity signal comes from invalid orbit rows.

This is a representation-level restraint, not a gate/selector.

## Robustness Condition

For the same `base_instance_id` across permutation variants:

- `P^{-1} adapted_mu(P(CNF))` should align with `adapted_mu(CNF)`;
- `P^{-1} adapted_rho(P(CNF))` should align with `adapted_rho(CNF)`;
- adapter deltas `adapted - static` should align in direction and ranking;
- search-improving and search-worsening permutation variants should not receive
  indistinguishable positive treatment.

## Proposed Loss Terms

`objective_score` for offline proxy:

```text
search_delta_reward
- permutation_inconsistency_penalty
- invalid_orbit_identity_penalty
- non_symmetric_perturbation_penalty
- adapter_delta_magnitude_penalty
```

Training-side loss terms, all default-off:

- `permutation_consistency_loss`: variable-level adapted `mu/rho` alignment under metadata permutations.
- `permutation_delta_consistency_loss`: variable-level adapter-delta `mu/rho` alignment under metadata permutations.
- `valid_orbit_identity_loss`: positive distillation only on valid event-orbit masks.
- `negative_guard_loss`: pull adapter output back to static/base output for non-symmetric or no-valid-orbit rows.
- `adapter_delta_magnitude_loss`: bound adapter delta magnitude to reduce over-amplification.

## Offline Proxy Acceptance

The v1 proxy should classify the current diagnostic cases as follows:

- `dominating_set_hex_3x6_s4`: partial aligned; should receive medium positive or mixed signal, not a hard negative.
- `subset_cardinality_bw12::base`: search improves; should receive positive signal.
- `subset_cardinality_bw12::perm_seed1731`: search improves; should receive positive signal.
- `subset_cardinality_bw12::perm_seed1730`: valid orbit has signal but search worsens; should be penalized.
- random controls: should be suppressed by negative guard; random-control search changes are not positive examples.

## Unit/Smoke Acceptance

Before any adapter-only retrain:

- `py_compile` passes.
- unit tests cover no-valid-orbit negative guard, explicit non-symmetric guard,
  adapter delta magnitude penalty, and permutation delta consistency.
- one tiny synthetic adapter batch can compute and decrease the configured loss.

## Later Targeted Re-Audit

Only after the above passes:

- retrain adapter-only on targeted candidates + controls in a tiny smoke run;
- rerun targeted mechanism audit, not full runtime;
- check subset permutation split, random-control perturbation, hex conflict behavior,
  and valid-orbit concentration.

Gate/selector remains explicitly postponed.
