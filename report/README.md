# Concrete Strength DE–SVR report

Self-contained editable LaTeX report. The BMSCE formatting package, institutional logo, figures and bibliography are included here; the external central template library is not required to build this copy.

From the repository root, build with `sh report/scripts/build.sh`. XeLaTeX, latexmk, Biber, biblatex and biblatex-ieee are required. The delivered PDF is `concrete-strength-de-svr-report.pdf`. Metadata is in `metadata.tex`; content is split by chapter. Figures and generated tables derive from frozen `results/final/` evidence. See `../docs/deliverable-validation.md` for checks and scope.

Uses BMSCE typography and margins with the stock-price example's section order, adapted to concrete prediction. Preserves headings for unperformed analyses and explicitly states their limits. Adds the required Comparative Performance Analysis, Applications and Case Studies, References and GitHub Repo Link sections absent or incomplete in the sample. Certificate signature fields remain blank for actual endorsement.

To use Overleaf, upload this directory’s contents, select XeLaTeX and use `main.tex` as the main document. The body font is Latin Modern (Computer Modern), bundled with TeX Live and Overleaf.
