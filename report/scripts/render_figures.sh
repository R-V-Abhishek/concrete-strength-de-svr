#!/bin/sh
# Compile each TikZ figure in report/figures/ on its own page, then crop it to a 600-dpi PNG
# (report/assets/NAME.png) for the presentation. The report itself \input's the .tex directly.
set -eu
cd "$(dirname "$0")/.."
mkdir -p build/figures
for name in architecture de-flowchart; do
  cat > "build/figures/$name-wrap.tex" <<TEX
\documentclass[12pt]{article}
\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{fontspec,amsmath,amssymb,xcolor,tikz}
\usetikzlibrary{positioning,arrows.meta,fit,backgrounds,calc,shapes.geometric}
\setmainfont{Times New Roman}
\pagestyle{empty}
\begin{document}
\input{../../figures/$name.tex}
\end{document}
TEX
  (cd build/figures && xelatex -interaction=nonstopmode -halt-on-error "$name-wrap.tex" >/dev/null)
  uv run --script scripts/crop_png.py "build/figures/$name-wrap.pdf" "assets/$name.png"
done
