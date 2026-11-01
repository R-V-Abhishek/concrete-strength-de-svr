#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export TEXINPUTS=".:./latex//:${TEXINPUTS:-}"
if [ -n "${BIBER:-}" ]; then
  latexmk -g -xelatex -e '$biber = "'"$BIBER"' %O %B";' -interaction=nonstopmode -halt-on-error -outdir=build main.tex
else
  latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
fi
