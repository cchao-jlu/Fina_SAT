# Next Stage Plan

Date: 2026-06-27

## Current Status

The current EchoSAT / SAT symmetry line should remain conservative:

- The stable runtime path is still patched `pre=true` weighted Glucose.
- `weighted_no_pre` is diagnostic only and must not enter main runtime tables.
- Canonical low-warmup targeted acceptance shows that `v1.2 iter=15.pt` remains the best runtime candidate.
- `v1.7 iter=50/80/115.pt` improved parts of the offline reward story, but did not beat `v1.2 iter=15.pt` on targeted acceptance.
- The core success metric is adapter-vs-cached search work: decisions/conflicts reduction under symmetry evidence.
- Protocol-time speedup over plain Glucose is not established and should not be claimed.

## Main Judgment

Do not continue long GRPO training yet.

The next stage is a failure-attribution and objective-repair stage. The issue is not benchmark coverage or selector design. The current evidence says the objective can pass offline reward replay while still failing targeted runtime acceptance, especially on hard negatives and low-warmup stability.

## Stage 1: v1.7 Runtime Failure Attribution

Compare these checkpoints under the existing canonical low-warmup targeted acceptance artifacts:

- `v1.2 iter=15.pt`
- `v1.7 iter=50.pt`
- `v1.7 iter=80.pt`
- `v1.7 iter=115.pt`

Required analysis:

- Per-base and per-variant adapter-vs-cached decisions/conflicts deltas.
- Hard-negative recovery failures on `k10_color9` and `php_p10_h9`.
- Anchor preservation on `k9_color8` and `php_p9_h8`.
- Random-control suppression, especially where protocol-time improves but search work worsens.
- Whether wc1 and wc3 disagree because the objective is overfit to wc1 or because event signal becomes unstable as warmup grows.

Expected output:

- A short attribution report in `docs/`.
- CSV summaries under `runs/analysis/`.
- No new solver benchmark expansion.
- No training.
- No gate/selector.

## Stage 2: Training vs Runtime Objective Mismatch Audit

Use the training replay tables and targeted runtime tables to identify where offline reward and runtime acceptance disagree.

Questions to answer:

- Which samples get positive reward offline but fail adapter-vs-cached search-work acceptance?
- Are hard-negative rows receiving positive GRPO advantage because group normalization makes them "less bad"?
- Are anchor rows preserved because the policy actually learned symmetry guidance, or because they are easy under generic perturbation?
- Are random controls fully clamped in both reward and advantage, not just in raw reward?
- Does best-checkpoint selection match the strict runtime acceptance metric?

The output should make it clear whether the failure is in:

- reward component weights,
- GRPO group construction,
- checkpoint selection,
- dataset composition,
- or the low-warmup event signal itself.

## Stage 3: v1.8 Objective Repair

Only after the mismatch audit, implement a v1.8 objective. The likely direction is:

- Keep `v1.2 iter=15.pt` behavior as the baseline to preserve.
- Treat `v1.7` failed hard-negative behavior as negative training evidence.
- Make hard-negative recovery variant-level, not only averaged across base/family.
- Clamp random-control positive advantage to `<= 0`.
- Penalize CPU-only wins when decisions/conflicts worsen.
- Add a consistency penalty across wc1 and wc3.
- Keep CPU as a small tie-breaker only after decisions and conflicts both improve.

Do not add a learned gate or selector in v1.8. The adapter policy itself must first become stable on canonical paired cases.

## Stage 4: Dry-Run Before Any Formal Training

Before formal v1.8 training, run offline reward replay and require:

- `k9_color8` and `php_p9_h8` remain positive.
- `k10_color9` and `php_p10_h9` receive stronger recovery pressure than in v1.7.
- `subset_cardinality_bw12::perm_seed1730` remains negative.
- random controls have zero positive reward and non-positive advantage.
- CPU-only wins do not produce positive symmetry reward.
- near-cap or weighted-path-risk rows cannot become positive examples.

If these checks fail, do not train.

## Stage 5: Formal Training and Acceptance

If v1.8 dry-run passes, run one formal training job locally. After training:

- Do targeted acceptance first, not a large benchmark.
- Compare against `v1.2 iter=15.pt`, not only against the new `best.pt`.
- Use wc1 as the primary budget and wc3 as stability diagnostic.
- Continue to report protocol time, but do not use it as the success criterion.

Acceptance target:

- Anchor search-ok fraction remains 1.0.
- Hard-negative wc1 search-ok fraction improves over v1.7 and reaches at least the `v1.2 iter=15.pt` level.
- Random-control search-ok stays near zero.
- `subset_cardinality_bw12::perm_seed1730` remains negative.
- All known expected labels still match.
- All rows remain on `patched_pretrue_main`, with `weighted_no_pre=False`.

## What Not To Do Next

- Do not expand the benchmark yet.
- Do not train a gate or selector yet.
- Do not claim solver speedup.
- Do not use random-control wins as positive evidence.
- Do not select checkpoints by protocol-time improvement.

## Current Candidate To Preserve

Use `v1.2 iter=15.pt` as the current conservative runtime candidate until a later objective beats it on targeted acceptance.
