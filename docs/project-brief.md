# Project brief

## Selected topic

Concrete Compressive Strength Prediction Using Differential Evolution–Optimized Support Vector Regression.

## Question

Does DE tuning reduce SVR prediction error relative to default settings, and how does it compare with random search under an equal candidate-evaluation budget?

## Scope

- Use the existing UCI dataset without collecting, labelling, or synthesizing data.
- Use one primary model: RBF-SVR.
- Optimize `C`, `gamma`, and `epsilon`; finalize ranges after baseline inspection.
- Implement standard DE operators explicitly so the bio-inspired algorithm can be explained and assessed.
- Compare default SVR, random-search SVR, and DE-SVR.
- Prioritize reproducible experiments, plots, report, and PPT.
- An application UI, additional optimizers, and extra datasets are outside the initial scope.

## Evaluation rules

- Inspect duplicate rows and repeated mixture/age combinations before finalizing splits; document the handling policy.
- Reserve a test set before optimization. Never use test results as optimizer fitness.
- Fit scaling inside each training/validation fold using an ML pipeline.
- Use identical validation folds and search spaces for random search and DE.
- Count all evaluated candidates, including the DE initial population, in the tuning budget.
- Use validation RMSE as the proposed fitness; report test RMSE, MAE, and R².
- Repeat searches across fixed random seeds and report variability, runtime, and convergence against evaluations.
- Treat published numbers as literature context unless their data splits and evaluation protocols are reproduced.
- Report measured outcomes honestly, including cases where DE does not outperform random search.

## Four-member responsibilities

The project proceeds sequentially, with one owner completing their stage and work log before handing over to the next person:

1. Sushanth S (1BM23CD063): setup, dataset validation, preprocessing, split manifests, evaluation, default SVR, random search, and administrative checks.
2. R V Abhishek (1BM23CD047): DE implementation, optimizer tests, integration, pilot timing, and protocol freeze.
3. Ullas N (1BM23CD067): final experiments, holdout evaluation, analysis, plots, and reproducibility checks.
4. Vedantha V V (1BM23CD069): report and PPT from the preceding members' logs/results, artifact quality checks, rehearsal coordination, and submission.

The first three members preserve explanations, commands, sources, decisions, and results in `docs/work-log.md`. Vedantha writes both final deliverables from that evidence. All four rehearse and present. The [implementation plan](implementation-plan.md) defines the sequential tasks, handoffs, verification, and blockers/enablers.

## Literature starting points

- UCI dataset and original readme: `../data/raw/Concrete_Readme.txt`.
- Yeh (1998), original strength-modelling study cited in the dataset documentation.
- “AI-Based Inference System for Concrete Compressive Strength: Multi-Dataset Analysis of Optimized Machine Learning Algorithms”: <https://www.mdpi.com/2076-3417/15/23/12383>. Inspect its UCI-specific protocol and results before using any numerical benchmark.

## Rubric alignment

The professor's rubric assigns 4 marks to dataset/problem definition, 6 to ML/DL model development, 10 to nature-inspired optimization, 6 to experimental analysis, and 4 to report/presentation/code documentation. Preserve baseline comparisons, explicit DE operators, and reproducible results as core deliverables.
