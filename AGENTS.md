# Repository instructions for coding agents

These instructions apply to this repository and all its subdirectories. Read this
file before editing anything. Follow the user's current request and any applicable
higher-priority instructions; use this file for the project's standing conventions.

## Read before editing

1. Inspect `git status --short --branch` and the relevant implementation, tests and
   files. Preserve unrelated changes. Fetch before syncing with remote work; never
   reset, force-push or overwrite another member's work to resolve a conflict.
2. Read [README.md](README.md), [the technical handoff](docs/technical-closeout.md),
   and the relevant stage in [the work log](docs/work-log.md).
3. For model/data/experiment changes, also read [the frozen protocol](docs/protocol.md)
   and [results guide](results/README.md).
4. For report or slide work, also read [the submission checklist](docs/submission-checklist.md)
   and [implementation plan](docs/implementation-plan.md). Inspect the supplied
   examples for structure, and use actual saved project evidence for content.

Inspect accessible files, Git history, logs and tools yourself before asking the
user for information. Keep searches narrow and output bounded. Prefer `rg` for
file/text searches. Make the smallest coherent change that satisfies the request.

## Project state and ownership

This is a four-member Bio-Inspired Algorithms AAT project titled **Concrete
Compressive Strength Prediction Using Differential Evolution–Optimized Support
Vector Regression**. One UCI numerical dataset, one RBF-SVR model, default/random
search baselines, and explicitly implemented DE are sufficient for the scope.

The workflow is sequential, not parallel:

| Stage | Owner | USN | Work |
|---|---|---|---|
| 1 | Sushanth S | 1BM23CD063 | Data, preprocessing, splits, baseline and Random Search |
| 2 | R V Abhishek | 1BM23CD047 | DE implementation, tests and pilot |
| 3 | Ullas N | 1BM23CD067 | Final experiments, evaluation and plots |
| 4 | Vedantha V V | 1BM23CD069 | Report, PPT and submission checks from saved logs/results |

Stages 1–3 and technical closeout were completed at tag
`technical-closeout-2026-10-27`. Consult current files and later work-log entries
for progress after that snapshot. Report/PPT and administrative completion must
be verified independently. Do not add agents, worktrees, integration frameworks,
new datasets, models, optimizers or a UI unless the current task needs them.

## Preserve experimental integrity

- Preserve `data/raw/`, `data/source/` and `references/`. Retain dataset attribution.
  The reference report/PPT describe a different stock-price project: never copy
  their identities, certificate details, results or unsupported claims.
- `docs/technical-closeout.md` and `results/final/final_results.json` define the
  frozen report evidence. Keep pilot and final results separate. Distinguish
  validation-selected demonstration metrics from five-seed aggregate metrics.
- Both tuned methods substantially improve default SVR; DE and Random Search
  have essentially equivalent holdout performance here. Do not claim significant
  superiority, fabricate improvement, cherry-pick seeds or select on holdout error.
- Keep the saved group-disjoint holdout/CV splits, fold-local scaling, log-parameter
  search bounds and equal initialization-inclusive budgets. The learning curve
  uses three development-only folds, nested whole-group samples and both training
  and validation RMSE. Read the protocol for exact parameters.
- The original baseline/Random Search holdout scores were already evaluated in
  Stage 1. Never describe the entire process as using a previously unseen holdout.
- Original runs used Windows and different library versions from locked macOS
  verification. Preserve original provenance. The verifier explicitly handles
  Windows paths and CRLF/LF text hashes; binary source hashes must match exactly.
- Change frozen protocol/evidence only when required by the current task. Record
  the reason, preserve the historical result, rerun affected checks/experiments,
  update dependent figures/documents and checksum manifests, and use a new freeze
  tag. Never move or overwrite the existing technical tag.

## Implementation and verification

- Use the independent project in this repository, not the parent BIO lab's
  environment. Python requirement is in `pyproject.toml`; use `uv`, `uv add` and
  `uv run`. Preserve `uv.lock` and avoid unrelated dependency upgrades.
- Use straightforward Python and modern type hints. Do not add
  `from __future__ import ...`. Understand interfaces rather than adding guessed
  schemas, repeated `getattr`/`hasattr`/`isinstance` branches or broad fallbacks.
- DE operators live in `src/concrete_strength/de.py`; the shared CV evaluator is
  in `evaluation.py`. Follow existing contracts and inspect their tests first.
- Run the narrowest relevant tests, then the full suite when changing shared
  experimental behavior. Inspect actual outputs and the diff; fix discovered
  problems before reporting completion. Never claim an unperformed check passed.

```sh
uv sync --locked
uv run pytest -q
uv run concrete-strength verify-stage1
uv run concrete-strength verify-evidence --output-path /tmp/concrete-evidence-verification.json
shasum -a 256 -c results/final/SHA256SUMS
```

The evidence verifier refits all five fixed DE selections and checks saved metrics;
it does not rerun optimization. The alternate output path preserves the frozen
verification record. A sandbox may need writable `UV_CACHE_DIR`/`MPLCONFIGDIR`
locations; do not change global shell configuration to solve a local cache issue.

Do not run training merely to edit prose or formatting. Full reproduction uses
separate output directories as documented in `results/README.md`. Commands such
as `refresh-diagnostics` intentionally rewrite tracked evidence; use them only
when the task calls for regeneration, then check provenance and checksums.

## Report, presentation and handoffs

- Put report sources/final PDF in `report/` and editable PPTX in `presentation/`.
  Cover every mandatory section/heading in the professor's checklist.
- Use the current evidence, exact team names/USNs, correct units, real citations
  and clearly described aggregation. Verify guide/course/year/signatory details;
  do not invent them or inherit them from examples.
- Render and inspect every report page and slide after layout changes. Use the
  available document/PDF/presentation skills where applicable. Check all displayed
  numbers against saved results and preserve editable sources.
- Record substantive implementation, experiment or deliverable changes in
  `docs/work-log.md`: decisions, commands, actual verification, artifacts and
  remaining blockers. The final writer must be able to use the logs without
  reconstructing undocumented work.
- Do not mark registration, signatures, Drive upload, professor access or the
  presentation complete without evidence. A private repository URL alone does
  not provide professor access. External messages, invitations, publication and
  uploads need authorization from the current task or prior user instructions.
- Use small commits and inspect staged changes before committing. Prefer a short
  `codex/` branch and a PR for collaborative changes; keep this proportional to
  the task. Push when requested, preserve teammates' branches, and never commit
  credentials, caches, virtual environments or build outputs.
- Report concisely what changed, verification performed and any real remaining
  issue. Use session-wide `f1`, `f2`, … for suggested follow-ups and `q1`, `q2`, …
  for questions; do not add follow-ups just as conversational padding.
