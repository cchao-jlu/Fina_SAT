# Glucose Weighted Preprocessing Code Audit

## Scope

This audit compares `solvers/glucose` and `solvers/glucose_weighted` after the solver protocol attribution isolated the loss rows to the weighted Glucose path. It focuses on:

- `simp/Main.cc`
- `simp/SimpSolver.h`
- `simp/SimpSolver.cc`
- `core/Dimacs.h`
- `core/Solver.h`
- `core/Solver.cc`

This is not a solver speedup claim. The purpose is to locate why the weighted binary can return `INDETERMINATE` with 0 decisions and 0 conflicts on symmetry protocol loss cases.

## Behavioral Evidence

The failing base instances are:

- `dominating_set_hex_4x5_s5`
- `vertex_cover_torus_4x5_norat`

The weighted-path audit showed:

| probe | result |
| --- | --- |
| plain Glucose, original input | solved |
| plain Glucose, extra `c weight` comment | solved |
| weighted Glucose, no `c weight` line | `INDETERMINATE`, 0 decisions, 0 conflicts |
| weighted Glucose, all `+1.0` weights | `INDETERMINATE`, 0 decisions, 0 conflicts |
| weighted Glucose, all `-1.0` weights | `INDETERMINATE`, 0 decisions, 0 conflicts |

The follow-up preprocessing probe:

| base_instance_id | probe | result | simplification time | decisions | conflicts |
| --- | --- | --- | --- | --- | --- |
| `dominating_set_hex_4x5_s5` | plain pre, 5s | SAT | 2.41s | 8 | 0 |
| `dominating_set_hex_4x5_s5` | weighted pre, 5s | INDETERMINATE | 4.91s | 0 | 0 |
| `dominating_set_hex_4x5_s5` | weighted no-pre, 5s | SAT | n/a | 15 | 0 |
| `dominating_set_hex_4x5_s5` | weighted no-elim, 5s | INDETERMINATE | 4.91s | 0 | 0 |
| `dominating_set_hex_4x5_s5` | weighted no-lcm, 5s | INDETERMINATE | 4.91s | 0 | 0 |
| `dominating_set_hex_4x5_s5` | weighted pre, 30s | SAT | 19.86s | 8 | 0 |
| `vertex_cover_torus_4x5_norat` | plain pre, 5s | UNSAT | 4.95s | 15 | 16 |
| `vertex_cover_torus_4x5_norat` | weighted pre, 5s | INDETERMINATE | 4.65s | 0 | 0 |
| `vertex_cover_torus_4x5_norat` | weighted no-pre, 5s | UNSAT | n/a | 15 | 16 |
| `vertex_cover_torus_4x5_norat` | weighted no-elim, 5s | INDETERMINATE | 4.66s | 0 | 0 |
| `vertex_cover_torus_4x5_norat` | weighted no-lcm, 5s | INDETERMINATE | 4.67s | 0 | 0 |
| `vertex_cover_torus_4x5_norat` | weighted pre, 30s | INDETERMINATE | 29.68s | 0 | 0 |

Interpretation:

- The `c weight` line is not sufficient to reproduce the loss.
- The weighted binary without weights is sufficient to reproduce the loss.
- `-no-pre` restores search and solves both base instances under 5s.
- `-no-elim` and `-no-lcm` do not restore search; the loss is not isolated to only variable elimination or LCM.
- Weighted preprocessing/simplification is much slower than plain preprocessing on the same CNFs and can consume the CPU limit before any search decision.

## Code Diff Findings

### `simp/Main.cc`

Relevant shared control flow:

1. CPU limit is installed with `setrlimit`.
2. During parsing, `SIGXCPU` uses `SIGINT_exit`.
3. After parsing, `SIGXCPU` switches to `SIGINT_interrupt`, which calls `solver->interrupt()`.
4. `S.eliminate(true)` runs preprocessing.
5. `S.solveLimited(dummy)` starts search.

Weighted-specific differences:

- Adds event stats printing when `collectEvents` is enabled.
- Adds `-conf-lim`, applied before `solveLimited`.
- Does not otherwise change the preprocessing call site.

This means the loss is not explained by a different `Main.cc` preprocessing call. Both binaries call `S.eliminate(true)` when `pre=true`.

### `simp/SimpSolver.*`

The only source-level diff in `SimpSolver` is the `newVar` signature:

```cpp
Var SimpSolver::newVar(bool sign, bool dvar, double weight_init, double weight_scale) {
    Var v = Solver::newVar(sign, dvar, weight_init, weight_scale);
```

The simplification loop itself is effectively identical:

- `eliminate()` starts with `simplify()`.
- It loops over touched clauses, backward subsumption, and the elimination heap.
- It checks `asynch_interrupt` during preprocessing.
- It calls `rebuildOrderHeap()` and `garbageCollect()` when `turn_off_elim=true`.

This makes `SimpSolver` an unlikely direct source of the behavioral divergence unless the weighted `Solver::newVar` state changes the cost of the same simplification path.

### `core/Dimacs.h`

Weighted parser adds `c weight` handling:

```cpp
double weight = parsePlainDouble(in);
bool sgn = weight > 0;
weight = (weight > 0) ? weight : -weight;
S.newVar(!sgn, true, weight, weight);
printf("%f\n", weight);
```

Observations:

- Positive weights call `newVar(false, ...)`; negative weights call `newVar(true, ...)`.
- The parser prints one bare float per variable, which pollutes stdout and adds small overhead.
- However, the loss reproduces with `weighted_glucose_no_weight`, where this block does not run.

Therefore `Dimacs.h` weight parsing is not the primary failure condition for the current loss rows.

### `core/Solver::newVar`

Plain:

```cpp
activity.push(rnd_init_act ? drand(random_seed) * 0.00001 : 0);
```

Weighted:

```cpp
activity.push(rnd_init_act ? drand(random_seed) * 0.00001 : weight_init);
var_weight_init.push(weight_init);
var_weight_scale.push(weight_scale);
```

When there is no `c weight` line, default `weight_init=0.0` and `weight_scale=1.0`, so this should be behaviorally close to plain initialization. With all `+1.0` or all `-1.0`, initial activity is nonzero and bump scaling changes, but those are not required to reproduce the loss.

### `core/Solver::pickBranchLit`

Plain:

```cpp
next = order_heap.removeMin();
```

Weighted:

```cpp
next = order_heap.removeAt(0);
```

For heap index 0 these should usually return the same variable, though `removeAt(0)` is a custom addition in the weighted heap. This matters for search behavior, but it does not explain the current 0-decision losses because search never reaches a decision.

### `core/Solver::search`

Weighted adds a budget check at the top of the infinite search loop:

```cpp
for (;;) {
    if (!withinBudget())
        return l_Undef;
```

Plain does not check `withinBudget()` before the first propagation and decision in `search()`. Both versions check `withinBudget()` after each `search()` call in `solve_()`.

This is the strongest code-level suspect for the observed 0-decision `INDETERMINATE` rows:

1. `S.eliminate(true)` can spend nearly the whole CPU limit.
2. `SIGXCPU` after parsing is routed to `SIGINT_interrupt`, setting `asynch_interrupt=true`.
3. Weighted `search()` immediately checks `withinBudget()`.
4. `withinBudget()` returns false when `asynch_interrupt=true`.
5. Weighted returns `l_Undef` before propagation or decisions.

This matches the observed stats: `INDETERMINATE`, 0 decisions, 0 conflicts.

## Current Diagnosis

The immediate issue was weighted preprocessing plus interrupt/budget handling:

- Weighted preprocessing is much slower than plain on the loss CNFs.
- When the CPU limit is consumed or nearly consumed in preprocessing, the weighted search loop could return before the first decision.
- The adapter is not implicated.
- Static learned weights are not implicated.
- The `c weight` input line is not the necessary trigger.

## Patch

The weighted solver has been patched to match plain Glucose's search-loop budget placement:

- Removed the extra top-of-loop `withinBudget()` check from `solvers/glucose_weighted/core/Solver.cc`.
- Kept the existing `solve_()` budget check after each `search()` call.
- Rebuilt `solvers/glucose_weighted/simp/glucose_static`.

This means weighted Glucose no longer exits before the first propagation/decision solely because preprocessing consumed the CPU budget. The outer budget check remains in place for solver-level limits.

## Patch Validation

Targeted pre=true checks after rebuilding `glucose_static`:

| base_instance_id | command path | result | simplification time | decisions | conflicts |
| --- | --- | --- | --- | --- | --- |
| `dominating_set_hex_4x5_s5` | weighted pre, 5s | SAT | 4.92s | 15 | 0 |
| `vertex_cover_torus_4x5_norat` | weighted pre, 5s | UNSAT | 4.74s | 15 | 16 |

Formal weighted-path audit after the patch:

| base_instance_id | rows | weighted no-weight solved | all +1.0 solved | all -1.0 solved | indeterminate rows |
| --- | --- | --- | --- | --- | --- |
| `dominating_set_hex_4x5_s5` | 45 | yes | yes | yes | 0 |
| `vertex_cover_torus_4x5_norat` | 45 | yes | yes | yes | 0 |

Artifacts:

- `runs/analysis/symmetry_weighted_glucose_path_audit.csv`
- `runs/analysis/symmetry_weighted_glucose_path_audit_by_base.csv`
- `docs/symmetry_weighted_glucose_path_audit.md`
- `runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv`
- `runs/analysis/symmetry_solver_protocol_preflight_guided_loss_diagnostics.csv`
- `docs/symmetry_solver_protocol_preflight.md`
- `runs/analysis/symmetry_solver_protocol_preflight_weighted_no_pre_per_instance.csv`
- `docs/symmetry_solver_protocol_preflight_weighted_no_pre.md`

The refreshed audit now labels both former loss bases as `weighted_path_loss_not_reproduced`.
The patched original repeated paired protocol also has 855/855 solved method rows, 0 guided-loss diagnostics rows, and 171/171 attribution rows labelled `event_collection_overhead_only`.

## Patched Protocol Roles

The runtime protocol now separates the main and diagnostic solver paths:

| protocol | solver_path_role | weighted no-pre | rows | solved rows | indeterminate rows | guided-loss rows | attribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| patched `pre=true` main | `patched_pretrue_main` | false | 855 | 855 | 0 | 0 | 171/171 `event_collection_overhead_only` |
| no-pre preprocessing diagnostic | `weighted_no_pre_diagnostic` | true | 855 | 855 | 0 | 0 | 171/171 `event_collection_overhead_only` |

The `--weighted-no-pre` run is a diagnostic path only. It is useful for isolating
preprocessing effects, but it is not merged with the main runtime protocol and is
not used as a solver speedup claim.

Patched `pre=true` representation checks were also refreshed:

| audit | result |
| --- | --- |
| direct event orbit audit | 165/165 valid rows are event-positive; 0 missing-event rows |
| cached W05 adapter audit | mean valid adapter gain 0.3479 |
| negative-case audit | 6 no-activity event-nonzero rows; 0 adapter violations |
| variable-level permutation alignment | static `mu` MAE 1.52e-08; adapted `mu` MAE 0.2573 |

## Remaining Caveats

- This is not a solver speedup claim.
- `glucose_weighted` preprocessing is still materially slower than plain Glucose on `dominating_set_hex_4x5_s5`.
- The all-positive neutral weighted path solves after the patch but can change search work substantially, especially on `dominating_set_hex_4x5_s5`.
- `--weighted-no-pre` remains a separately labelled diagnostic path; the patched pre=true weighted path is the current main protocol path.
