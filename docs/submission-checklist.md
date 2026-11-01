# AAT submission checklist

Transcribed from the professor's instructions supplied in chat. Dates are retained as stated; the message did not specify a year.

## Administration

- [ ] Register four group members and the selected AAT title in the [registration sheet](https://docs.google.com/spreadsheets/d/1qJdlb0Gn3ZuhiawFJYLXDUS3Ovxf_J_SjEr1bWrXcPI/edit?usp=sharing). The original message requested registration by EOD.
- [ ] Present on or before 05 November; 31 October BIO lab hours were offered as a presentation opportunity.
- [x] Prepare both PPT and project report; both are mandatory for SEE.
- [ ] Upload both files in one folder named with the AAT title to the [submission folder](https://drive.google.com/drive/folders/1Ap_3JzDs8Xdv40QsXLYkSlMmOLaC4F_o?usp=drive_link).
- [ ] Include the GitHub repository link in the report and arrange access for the professor if the repository is private.

## Required PPT slide titles

- [x] Cover Slide/Main Slide
- [x] Introduction to Optimization Problems
- [x] What are Nature-Inspired Algorithms?
- [x] Classification of Nature-Inspired Algorithms
- [x] Problem Statement
- [x] Implementation and Results
- [x] Performance Metrics and Benchmarking
- [x] Advantages and Limitations
- [x] Future Scope
- [x] References

## Required report sections

- [x] Cover Page
- [x] Certificate Page
- [x] Acknowledgement
- [x] Abstract
- [x] Table of Contents
- [x] Introduction
- [x] Literature Review
- [x] Theoretical Background
- [x] Nature-Inspired Algorithms: Detailed Study
- [x] Methodology and Implementation
- [x] Experimental Setup and Test Functions
- [x] Results and Discussion
- [x] Comparative Performance Analysis
- [x] Applications and Case Studies
- [x] Conclusion
- [x] Future Work
- [x] References
- [x] GitHub Repo Link

## Evidence to retain

- [x] Raw dataset provenance and preprocessing decisions
- [x] Baseline model configuration and results
- [x] DE operators, fitness definition, bounds, and evaluation budget
- [x] Default vs random-search vs DE comparison
- [x] Convergence curves, performance plots, and run metadata
- [x] Reproducible code and instructions

## Technical evidence status

Stage 3 technical evidence is complete and ready for report/PPT preparation:

- Final DE searches and frozen candidates: `../results/de/de_search_results.json`
- Final metrics, predictions, residuals, provenance and learning-curve data:
  `../results/final/final_results.json`
- Per-seed comparison table: `../results/final/metrics.csv`
- Convergence, holdout comparison, prediction/residual, and learning-curve
  plots: `../results/final/*.png`
- Reproduction commands and aggregate results: `../results/README.md`
- Stage-by-stage decisions and handoff: `work-log.md` and `protocol.md`

Report/PPT drafting and local rendering/validation are complete as recorded in
`deliverable-validation.md`. Certificate signatories and course/year details were
confirmed by the user. Actual signatures/endorsements, repository and Drive access,
uploading both deliverables, reopening uploaded files, and presentation/release
evidence remain pending.

Original rubric: `../references/rubrics/bio-aat-rubric.docx`.
