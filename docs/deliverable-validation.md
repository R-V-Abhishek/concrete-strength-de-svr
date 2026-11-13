# Report and presentation validation

Date: 1 November 2026. Local document preparation is complete; signatures, professor access, registration, upload and presentation are not claimed complete.

## Deliverables

- `report/concrete-strength-de-svr-report.pdf`: 49 pages (Extensions 1 and 2 added 5-11 Nov 2026; reference-style redesign 11 Nov); editable source in `report/main.tex`, `metadata.tex`, `chapters/`, `frontmatter/`, `tables/`, `assets/` and `latex/`.
- `presentation/concrete-strength-de-svr-presentation.pptx`: 28 editable slides (11 Nov 2026 rebuild: Extension 2, agenda with slide ranges, section footers, speaker notes); the PDF preview was rendered through Keynote, not PowerPoint. Rebuild source: `presentation/scripts/build_presentation.py`.
- Central library: `/Users/rva/Projects/BMSCE_Academic_Templates/`. The previous `BMSCE_Thesis_Guidelines_CSE_DS` folder is preserved completely at `archive/original-supplied-folder/` inside this renamed library.

The central library contains separate course-report and six-chapter thesis starters, one shared formatting package, references, and a reusable PowerPoint. It is a filesystem template library, not an installed Codex skill.

## Confirmed metadata

Guide: Prof. Manoj Kumar, Assistant Professor. HOD: Dr. Shyamala G. Course: Bio-inspired Algorithms, 23DS7BSBIO. Academic year: 2026–27. All four students and USNs match the repository. Certificate fields are blank for actual signatures.

## Formatting and reference coverage

(Layout and border details in this paragraph are superseded by the 11 November redesign section below.) The report uses A4, 1-inch text margins, Times New Roman 12pt, 1.5 spacing, 14pt bold chapter titles, 12pt bold section headings, 0.5-inch paragraph indentation, Roman front matter and Arabic main matter. Captions are single-spaced; tables are captioned above and figures below. Citations use BibLaTeX IEEE style with Biber. A medium-grey (`black!55`) double border, with a 2.4pt outer line inset 0.5 inches and a 1.2pt inner line inset 0.55 inches, rounded by 6pt and 3pt respectively, is present on **all 35 pages**, per the user's explicit override of the original `.tex`, which had disabled it for main matter. Running headers have additional clearance inside the border.

The stock-price example's main section order is preserved: Introduction; Literature Review; Theoretical Background; Nature-Inspired Algorithms: Detailed Study; Methodology and Implementation; Experimental Setup and Test Functions; Results and Discussion; Conclusion; Future Work. Topic-specific subsections are adapted from GA/LSTM/banking to DE/SVR/concrete. The required Comparative Performance Analysis and Applications and Case Studies chapters appear before the conclusion. References and GitHub Repo Link are explicit. Unlike the sample's erroneous `0.x` labels, chapters are numbered normally.

Sensitivity Analysis, Statistical Significance Testing, Temporal Performance Analysis, Hyperparameter Importance Analysis and Feature Importance Results headings are retained. They explicitly state what was not measured. No experimental evidence is invented to fill them. The 60–80 page / 30–50 reference targets in the attached instructions describe a final-year thesis; the current deliverable is the course AAT report, with ten relevant references.

The PPT preserves the supplied dimensions, institutional branding, masters and byte-identical theme parts. Its formatting adds bold navy titles, subordinate headings, varied type sizes and paragraph spacing. Slide 10 contains an editable native comparison table. Plots remain the frozen project PNGs; chart objects are not claimed to be editable.

## Verification performed

- Compiled the project report with XeLaTeX, latexmk and Biber: **no LaTeX warnings, undefined references or overfull boxes** in the final log.
- Rendered every project page and slide with Poppler/LibreOffice; visually checked cover/certificate, borders, header clearance, contents, equations, tables, plots and typography.
- Confirmed the border drawing in every PDF page content stream and A4 dimensions on all pages.
- Checked all required headings, four USNs, confirmed guide/HOD, absence of inherited reference identities and unresolved citation markers.
- Compared the PPT's native metric table against `results/final/final_results.json`; checked all ten report per-seed metric rows against `results/final/metrics.csv`.
- Ran first-party PPTX package, slide geometry, font and native-table validation: **zero findings and zero layout warnings**. Receipt: `docs/validation/presentation-finalization.json`.
- Built both reusable course-report and thesis starters separately using their documented script. Both compile with a sample guideline citation and no warning/overfull output.
- Verified all nine frozen evidence checksums with `shasum -a 256 -c results/final/SHA256SUMS`. No experiments or selected-model refits were rerun for document work.
- Machine-readable project checks: `docs/validation/deliverables.json`.

The bundled Artifact Tool could not load the PPT because its Node adapter package `@oai/granola/node` was absent. Targeted python-pptx edits preserved the existing objects, and first-party finalization ran with import verification explicitly skipped. Rendering was checked in LibreOffice, not native Microsoft PowerPoint. These limits do not affect the structural/font/table checks recorded in the receipt.

## Rebuilding

Report: `sh report/scripts/build.sh` from the repository root, with XeLaTeX, Biber and latexmk installed. Required packages include fontspec, geometry, setspace, titlesec, fancyhdr, graphicx, amsmath, amssymb, booktabs, tabularx, longtable, float, algorithm, algpseudocode, caption, etoolbox, tikz, eso-pic, listings, xcolor, biblatex, biblatex-ieee and hyperref. Times New Roman must be available. Set `BIBER` to an existing binary path if necessary. The starter `.latexmkrc` also supports Overleaf with XeLaTeX. The delivery PDF is a copy of `report/build/main.pdf`.

This session used missing TeX packages from `/tmp/bmsce-texmf` and Biber from `/tmp/bmsce-biber/bin/universal-darwin/biber`; these temporary paths are not required by the template and are not permanent installations. Existing global TeX and Python project dependencies were unchanged. Run `uv run --script presentation/scripts/build_presentation.py` to build the PPT with its pinned python-pptx dependency. It does not train models. Run `uv run --script scripts/validate_deliverables.py` to check report metadata/borders/citations, slide dimensions/theme, the native results table and artifact hashes. It prints JSON without rewriting tracked evidence; the TeX log check is skipped explicitly if the report has not been rebuilt locally.

## Still pending

Obtain actual student/faculty signatures and endorsements, confirm repository access for the professor, upload both deliverables, reopen uploaded files, and record presentation/submission evidence. No external upload or message was performed.


## Reference correction review

The dataset's formal citation uses 1998, as recommended by UCI; its 2007 donation date is distinct. The dataset entry prints its year and DOI. Holland is the linked 1992 MIT Press edition, with original publication in 1975 stated explicitly. The Random Search discussion attributes comparison with grid/manual search to Bergstra and Bengio; DE comparisons depend on this project's saved evidence. Yeh's original DOI and its generated PDF hyperlink are correct. These changes were rebuilt, rendered and validated without altering the experimental results or the 35-page / 18-slide counts.

Primary records checked: [UCI dataset citation](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength), [MIT Press edition](https://mitpress.mit.edu/9780262581110/adaptation-in-natural-and-artificial-systems/), [JMLR Random Search paper](https://www.jmlr.org/papers/v13/bergstra12a.html).


## Report redesign (11 November 2026)

At the user's request the report borrows the design of `recycleguard/docs/report/report.pdf` (Agentic AI course): navy `#003366` accent; "CHAPTER n" in navy above an uppercase centred bold title (unnumbered headings also uppercase and centred); 14.4pt bold section headings; double navy border (1.6pt outer, 0.5pt inner, square corners) replacing the grey rounded border; double navy rules under the italic right-aligned running header and above the footer in the main body; front matter shows only a centred page number; blue hyperlinks (`colorlinks`, `linktoc=all`) so the contents, list of figures and list of tables are visibly clickable; microtype; the reference's code-listing style; margins 1.25in left / 1in right; 1.5em paragraph indent. Footer clearance: bottom margin 1.2in, footskip 24pt, so the footer baseline sits about 0.3in above the inner border. Follow-up the same day, at the user's request: the body font is now Latin Modern (the OpenType form of Computer Modern; TeX Live and Overleaf bundle it) instead of Times New Roman, and the border is on the front matter only (11 pages), as in the reference. Body pages keep the double navy header/footer rules, with margins 1.25in left, 1in right/top and 1.2in bottom. `scripts/validate_deliverables.py` now checks the navy border. Rebuilt with a clean log (no warnings or over/underfull boxes), 49 pages. Second follow-up (13 November 2026), at the user's request: side margins are now equal (1.125in each, same text width) so the content is centred on the A4 page; the front-matter border is black with rounded corners (10pt outer / 6pt inner radius); the body header/footer rules are black. Chapter labels and the cover title remain navy. The validator checks the black rounded border. This rebuild used biblatex 3.21 / biblatex-ieee 1.4f, which italicises online/dataset titles instead of quoting them and places "doi:" after a full stop; the user accepted this reference styling.
