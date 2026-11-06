# Project presentation

`concrete-strength-de-svr-presentation.pptx` contains 24 editable slides adapted from the professor's example. `concrete-strength-de-svr-presentation.pdf` is the rendered offline preview. The reference file in `../references/examples/` remains unchanged.

From the repository root, rebuild with `uv run --script presentation/scripts/build_presentation.py`. Its inline metadata pins python-pptx in an isolated environment without changing the experiment dependencies. It reads the frozen final result JSON and plots; it does not rerun experiments. The reusable `bmsce-presentation-template.pptx` is included alongside the project deck.

Confirmed faculty/course metadata, structural and visual checks, and remaining administrative tasks are recorded in `../docs/deliverable-validation.md`. The metric comparison is an editable table; plot images reproduce the original evidence. All mandatory PPT headings are covered, with Advantages and Limitations on separate slides.
