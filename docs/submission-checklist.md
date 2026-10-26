# AAT submission checklist

Transcribed from the professor's instructions supplied in chat. Dates are retained as stated; the message did not specify a year.

## Administration

- [ ] Register four group members and the selected AAT title in the [registration sheet](https://docs.google.com/spreadsheets/d/1qJdlb0Gn3ZuhiawFJYLXDUS3Ovxf_J_SjEr1bWrXcPI/edit?usp=sharing). The original message requested registration by EOD.
- [ ] Present on or before 05 November; 31 October BIO lab hours were offered as a presentation opportunity.
- [ ] Prepare both PPT and project report; both are mandatory for SEE.
- [ ] Upload both files in one folder named with the AAT title to the [submission folder](https://drive.google.com/drive/folders/1Ap_3JzDs8Xdv40QsXLYkSlMmOLaC4F_o?usp=drive_link).
- [ ] Include the GitHub repository link in the report and arrange access for the professor if the repository is private.

## Required PPT slide titles

- [ ] Cover Slide/Main Slide
- [ ] Introduction to Optimization Problems
- [ ] What are Nature-Inspired Algorithms?
- [ ] Classification of Nature-Inspired Algorithms
- [ ] Problem Statement
- [ ] Implementation and Results
- [ ] Performance Metrics and Benchmarking
- [ ] Advantages and Limitations
- [ ] Future Scope
- [ ] References

## Required report sections

- [ ] Cover Page
- [ ] Certificate Page
- [ ] Acknowledgement
- [ ] Abstract
- [ ] Table of Contents
- [ ] Introduction
- [ ] Literature Review
- [ ] Theoretical Background
- [ ] Nature-Inspired Algorithms: Detailed Study
- [ ] Methodology and Implementation
- [ ] Experimental Setup and Test Functions
- [ ] Results and Discussion
- [ ] Comparative Performance Analysis
- [ ] Applications and Case Studies
- [ ] Conclusion
- [ ] Future Work
- [ ] References
- [ ] GitHub Repo Link

## Evidence to retain

- [ ] Raw dataset provenance and preprocessing decisions
- [ ] Baseline model configuration and results
- [ ] DE operators, fitness definition, bounds, and evaluation budget
- [ ] Default vs random-search vs DE comparison
- [ ] Convergence curves, performance plots, and run metadata
- [ ] Reproducible code and instructions

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

The following remain open for Stage 4: drafting and rendering the report/PPT,
verifying certificate/signature details, confirming repository and Drive
access, uploading both deliverables, reopening uploaded files, and recording
presentation/release evidence.

Original rubric: `../references/rubrics/bio-aat-rubric.docx`.
