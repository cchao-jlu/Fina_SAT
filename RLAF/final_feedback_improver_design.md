# Final Feedback Improver Version: Detailed Design Notes

## 1. Scope

This document explains the full set of changes from the earliest effective `global_state` feedback refinement version to the current final version in this repository.

The starting point is the first effective evaluation-time feedback refinement pipeline:

```text
GNN(graph) -> guidance_0
solver warmup(guidance_0) -> feedback
feedback -> graph-level global_state
GNN(graph, global_state) -> guidance_1
solver final(guidance_1)
```

The final version keeps this test-time structure, but changes training so that the model is explicitly trained as a **feedback-conditioned one-step improver**.


## 2. High-Level Goal

The core goal of this version is:

1. Preserve the original RLAF framework and solver-in-the-loop GRPO training.
2. Preserve the graph-level `global_state` refinement design instead of moving to node-level dynamic state.
3. Borrow the main training idea from the paper:

```text
Self-Supervised Transformers as Iterative Solution Improvers for Constraint Satisfaction
```

Specifically:

- train the model as a **single-step improver**
- deploy it with an iterative/refinement-style test-time pipeline

In our SAT-guidance setting, that means:

- training should teach the model how to improve guidance **conditioned on a solver feedback state**
- testing should still allow:

```text
GNN -> solver feedback -> GNN
```


## 3. Starting Version

The earliest effective version already had:

- `global_state_dim`
- a graph-level `global_state`
- evaluation-time warmup solve
- one extra GNN forward conditioned on `global_state`

This version did **not** train the model as a feedback improver. It only added feedback refinement during evaluation.

So training was still effectively:

```text
graph -> GNN -> guidance -> solver -> GRPO
```

and testing optionally became:

```text
graph -> GNN -> guidance_0
guidance_0 -> solver warmup -> feedback
feedback -> global_state
graph + global_state -> GNN -> guidance_1
guidance_1 -> solver final
```


## 4. Problem With the Starting Version

That starting version has an obvious mismatch:

- the model is trained as a one-shot policy from a static graph
- but tested as a feedback-conditioned refiner

So the second GNN call at test time uses a capability the model was not explicitly trained for.

That mismatch motivated the final training redesign.


## 5. Final Design Overview

The final version changes training into:

```text
warmup guidance
-> solver warmup
-> global_state
-> GNN(graph, global_state)
-> refined guidance samples
-> solver final
-> GRPO
```

The model is therefore optimized for:

```text
graph + solver feedback state -> better guidance
```

instead of only:

```text
graph -> guidance
```


## 6. Main Design Choices

### 6.1 Keep graph-level feedback

This version deliberately stays with:

- graph-level `global_state`
- readout-time conditioning

It does **not** introduce:

- node-level dynamic states
- per-layer feedback modulation
- solver event traces

This keeps the architecture change small and isolates the effect of training the model as a one-step improver.


### 6.2 Use single-step improver training

Instead of running two GNN calls inside training by default, the new version can construct a solver feedback state first, and only then run one learnable GNN forward.

This is the key paper-inspired change.


### 6.3 Optimize a composite objective

The earlier improver attempt optimized mostly `decisions`, which reduced search counts but did not reliably reduce CPU time.

The final version therefore adds a composite target:

```text
composite =
  w_cpu * log1p(CPU time)
  + w_conf * log1p(conflicts)
  + w_dec * log1p(decisions)
```

The default intended setting is:

```text
w_cpu = 1.0
w_conf = 0.2
w_dec = 0.0
```

This makes the reward explicitly care about runtime, not just search size.


## 7. New Training Modes

The final version supports the following feedback-state input modes.

### 7.1 `none`

Original RLAF training:

```text
graph -> GNN -> solver -> GRPO
```

No feedback state is used.


### 7.2 `random_warmup`

Random guidance is generated without using the GNN:

```text
random guidance
-> solver warmup
-> global_state
-> GNN(graph, global_state)
-> solver final
-> GRPO
```

This corresponds most directly to the "single-step improver from random initial state" idea.


### 7.3 `model_warmup`

Feedback state comes from the current model itself:

```text
GNN(graph) -> guidance_0
guidance_0 -> solver warmup -> global_state
GNN(graph, global_state) -> guidance_1
guidance_1 -> solver final
-> GRPO
```

This is more expensive because training uses two GNN forwards, but the warmup state distribution matches test time better.


### 7.4 `mixed_warmup`

The final recommended mode.

It mixes:

- `random_warmup`
- `model_warmup`

with a configurable probability:

```yaml
training.feedback_model_warmup_prob: 0.3
```

Meaning:

- `70%` random warmup
- `30%` model warmup

This was chosen to reduce train/test distribution shift while still keeping the paper-inspired random-state improver behavior.


## 8. Detailed Training Flow

With the final recommended configuration:

```yaml
training.feedback_input_mode: mixed_warmup
training.feedback_val_mode: model_warmup
training.target_stat: composite
model.global_state_dim: 6
```

the training pipeline is:

### Step 1. Sample a batch of CNF graphs

The base graph structure is unchanged.

### Step 2. Build feedback states

Depending on the mode:

- random guidance is generated, or
- the current GNN produces warmup guidance

Then solver warmup is run with:

```yaml
training.feedback_warmup_cpu_lim
```

### Step 3. Encode solver stats into `global_state`

The solver returns global statistics:

- `decisions`
- `conflicts`
- `propagations`
- `restarts`
- `CPU time`
- `Result`

These are encoded into a 6-dimensional graph-level state:

```text
[
  log1p(decisions),
  log1p(conflicts),
  log1p(propagations),
  log1p(restarts),
  log1p(CPU time),
  result_code
]
```

where:

- `SATISFIABLE -> 1`
- `UNSATISFIABLE -> -1`
- otherwise `0`

### Step 4. Attach `global_state` to each graph

Each graph gets:

```python
data.global_state = ...
```

### Step 5. Run the learnable GNN once

The model then predicts refined guidance conditioned on:

- the graph
- the attached `global_state`

### Step 6. Sample refined guidance

The usual policy sampling remains unchanged.

### Step 7. Run solver final solve

The refined guidance is passed to the SAT solver.

### Step 8. Compute GRPO advantage

Instead of using only `decisions`, the final version can use the composite target.


## 9. Detailed Test Flow

Evaluation still follows the original effective feedback-refinement structure:

```text
graph -> GNN -> guidance_0
guidance_0 -> solver warmup -> global_state
graph + global_state -> GNN -> guidance_1
guidance_1 -> solver final
```

So the final version preserves the earlier successful evaluation design, but now training is better aligned with it.


## 10. Code-Level Changes

### 10.1 `src/model/model.py`

This file already supported graph-level `global_state` from the earlier version, and remains the place where the model consumes feedback.

Relevant behavior:

- `global_state_dim` is stored on the model
- `data.global_state` is read in `_get_global_state(...)`
- `global_state` is concatenated before the final readout

For variable outputs:

```text
h_var = [h_neg, h_pos, global_state]
```

This version also includes a batch-shape fix:

- batched PyG graphs concatenate 1D `global_state` tensors into a flat vector
- the code now reshapes that flat vector into:

```text
[num_graphs, global_state_dim]
```

before indexing it per graph

This fixed the earlier runtime error:

```text
mat1 and mat2 shapes cannot be multiplied ...
```


### 10.2 `src/solving/state.py`

This file holds the graph-level feedback encoding utilities:

- `solver_stats_to_global_state(...)`
- `attach_global_state(...)`
- `attach_global_state_batch(...)`

It converts solver warmup statistics into the 6D state and attaches it to each graph.


### 10.3 `src/policy/evaluate.py`

New addition:

- `sample_random_var_params(...)`

This function creates random variable parameterizations without running the GNN.

It is used by `random_warmup` and `mixed_warmup`.


### 10.4 `train_rlaf.py`

This file contains the main new logic.

#### Added `add_composite_target(...)`

This function computes:

```text
composite =
  w_cpu * log1p(CPU time)
  + w_conf * log1p(conflicts)
  + w_dec * log1p(decisions)
```

and stores it as:

```python
solver_stats["composite"]
```

GRPO then uses this new column as its training target when:

```yaml
training.target_stat: composite
```

#### Added `build_feedback_state_loader(...)`

This function is the main training-state constructor.

Responsibilities:

- select warmup mode
- run solver warmup
- encode the resulting `global_state`
- build a DataLoader containing graphs with feedback states attached

It supports:

- `none`
- `random_warmup`
- `model_warmup`
- `mixed_warmup`

#### Validation flow updated

Validation can also use feedback states through:

```yaml
training.feedback_val_mode
```

The recommended setting is:

```yaml
training.feedback_val_mode: model_warmup
```

so validation matches test time.


### 10.5 `configs/config_train_rlaf.yaml`

Added fields:

```yaml
training:
  feedback_input_mode: none
  feedback_val_mode: none
  feedback_model_warmup_prob: 0.3
  feedback_warmup_cpu_lim: 1
  feedback_warmup_num_samples: 1
  feedback_random_weight: 1.0
  composite_cpu_weight: 1.0
  composite_conflicts_weight: 0.2
  composite_decisions_weight: 0.0

model:
  global_state_dim: 0
```

These defaults keep the original training behavior unchanged unless the new options are explicitly enabled.


## 11. Why Composite Reward Was Added

Earlier improver experiments showed:

- `decisions` and `conflicts` could go down
- but `CPU time` still went up

This happens because SAT solver runtime is not only controlled by search count.

It is possible to have:

- fewer conflicts
- fewer decisions
- but more expensive propagation/conflict analysis per step

So optimizing only `decisions` is not enough.

The composite objective was added specifically to force the model to trade off:

- runtime
- search effort

rather than only minimizing one search-count statistic.


## 12. Why Mixed Warmup Was Added

Using only `random_warmup` causes distribution shift:

### Training

```text
random guidance -> solver warmup -> feedback state
```

### Test

```text
model guidance -> solver warmup -> feedback state
```

These state distributions are different.

Using only `model_warmup` removes that mismatch but increases training cost and may reduce diversity.

`mixed_warmup` is a compromise:

- keeps the single-step improver flavor
- exposes the model to realistic test-time feedback states
- reduces over-specialization to random warmup states


## 13. Recommended Final Configuration

### Training

```bash
python train_rlaf.py \
  model_name=GNN_Glucose_3SAT_FeedbackImprover_Composite \
  model.global_state_dim=6 \
  training.feedback_input_mode=mixed_warmup \
  training.feedback_model_warmup_prob=0.3 \
  training.feedback_val_mode=model_warmup \
  training.feedback_warmup_cpu_lim=1 \
  training.target_stat=composite \
  training.composite_cpu_weight=1.0 \
  training.composite_conflicts_weight=0.2 \
  training.composite_decisions_weight=0.0 \
  solver.solver=glucose \
  dataset.train_path='data/training/3sat/*/*.cnf' \
  dataset.val_path='data/validation/3sat/*/*.cnf'
```

### Evaluation with feedback refinement

```bash
python evaluate_guided_solver.py \
  checkpoint='runs/GNN_Glucose_3SAT_FeedbackImprover_Composite/best.pt' \
  dataset.eval_path='data/test/3sat/350/*.cnf' \
  feedback_refinement.enabled=True \
  feedback_refinement.warmup_cpu_lim=1 \
  save_file=solver_stats_feedback_350.csv \
  | tee eval_feedback_improver_composite_350.log
```

### Evaluation without feedback refinement

```bash
python evaluate_guided_solver.py \
  checkpoint='runs/GNN_Glucose_3SAT_FeedbackImprover_Composite/best.pt' \
  dataset.eval_path='data/test/3sat/350/*.cnf' \
  feedback_refinement.enabled=False \
  save_file=solver_stats_no_feedback_350.csv \
  | tee eval_feedback_improver_composite_350_no_feedback.log
```


## 14. Interpretation of the Final Version

The final version should not be described as:

- a node-level dynamic GNN
- a fully iterative recurrent policy
- a solver-event-driven model

Instead, the correct description is:

> A graph-level, feedback-conditioned single-step guidance improver trained with solver-in-the-loop GRPO. The model uses a solver-derived global feedback state to refine guidance, with mixed warmup-state generation during training and a composite runtime-aware reward.


## 15. Remaining Limitations

This final version still has clear limits.

1. Feedback is graph-level, not node-level.
2. The model only sees aggregated solver statistics, not true solver event traces.
3. Feedback only enters at readout time, not inside message passing layers.
4. Mixed warmup reduces train/test mismatch, but does not eliminate it entirely.
5. The approach still depends on expensive solver calls during training.


## 16. Logical Next Step

If this version works well, the next strongest upgrade would be:

1. keep the same graph-level training setup
2. inject `global_state` into message passing, not only readout

Only after that would it be worth revisiting:

- node-level dynamic state
- solver event logs
- per-step recurrent refinement

