# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf"]
# ///
"""Crop the first PDF page to its drawn content and save a 600-dpi PNG."""
import sys
import pymupdf

src, dst = sys.argv[1:3]
page = pymupdf.open(src)[0]
rects = [d["rect"] for d in page.get_drawings()] + [b[:4] for b in page.get_text("blocks")]
box = pymupdf.Rect(rects[0])
for r in rects[1:]:
    box |= pymupdf.Rect(r)
page.get_pixmap(dpi=600, clip=box + (-6, -6, 6, 6)).save(dst)
