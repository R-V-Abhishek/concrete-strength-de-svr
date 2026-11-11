# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf==6.10.0", "python-pptx==1.0.2"]
# ///
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import ContentStream
from pptx import Presentation
import json,re,hashlib,zipfile,csv
root=Path(__file__).resolve().parents[1]
report=root/'report/concrete-strength-de-svr-report.pdf'
deck=root/'presentation/concrete-strength-de-svr-presentation.pptx'
r=PdfReader(report);p=Presentation(deck)
checks={}
checks['report_page_count']=len(r.pages)
checks['a4_every_page']=all(abs(float(x.mediabox.width)-595.276)<1 and abs(float(x.mediabox.height)-841.89)<1 for x in r.pages)
bordered=[]
for page in r.pages:
 ops=ContentStream(page.get_contents(),r).operations
 widths=[float(a[0]) for a,b in ops if b==b'w']
 navy=[tuple(round(float(v),2) for v in a) for a,b in ops if b==b'RG']
 moves=[tuple(round(float(v),1) for v in a) for a,b in ops if b==b'm']
 bordered.append(any(abs(x-1.59403)<.01 for x in widths) and any(abs(x-.49813)<.01 for x in widths) and (0,.2,.4) in navy and (34.0,34.0) in moves and (38.3,38.3) in moves)
front=[i for i,l in enumerate(r.page_labels) if l[0].lower() in 'ivx']
checks['border_on_every_front_matter_page']=all(bordered[i] for i in front) and not any(bordered[i] for i in range(len(bordered)) if i not in front)
checks['bordered_page_count']=sum(bordered)
checks['border_style']='Front matter only: double navy border (0,51,102), 1.6pt outer / 0.5pt inner; 1.2 / 1.35 cm insets; square corners'
text='\n'.join(x.extract_text() for x in r.pages)
compact=lambda s: re.sub('[^a-z0-9]','',s.lower())
normalized=compact(text)
heads=['Certificate','Acknowledgement','Abstract','Contents','Introduction','Literature Review','Theoretical Background','Nature-Inspired Algorithms: Detailed Study','Methodology and Implementation','Experimental Setup and Test Functions','Results and Discussion','Comparative Performance Analysis','Applications and Case Studies','Conclusion','Future Work','References','GitHub Repo Link']
checks['required_report_headings']=all(compact(h) in normalized for h in heads)
checks['identities_report_and_cover']=all(x in text and x in '\n'.join(s.text for s in p.slides[0].shapes if s.has_text_frame) for x in ['1BM23CD047','1BM23CD063','1BM23CD067','1BM23CD069','Manoj Kumar','Shyamala G'])
checks['no_unresolved_report_citations']='[?]' not in text and '??' not in text
checks['no_project_placeholder_prose']='Replace with' not in text
checks['no_em_dashes_report']='—' not in text
checks['no_em_dashes_ppt']='—' not in '\n'.join(x.text for slide in p.slides for x in slide.shapes if x.has_text_frame)
checks['no_stale_reference_identities']=all(s not in text for s in ['Shambhavi','Rajpurohit','Harshavardhan','Shreekar','Sampreeth'])
checks['report_contains_all_ten_run_metrics']=all(f"{float(x['rmse']):.4f}" in text and f"{float(x['mae']):.4f}" in text for x in csv.DictReader((root/'results/final/metrics.csv').open()))
log_path=root/'report/build/main.log'
if log_path.is_file():
 log=log_path.read_text()
 checks['report_clean_tex_log']=all(s not in log for s in ['Overfull','undefined references','LaTeX Warning','Package biblatex Warning'])
else:
 checks['report_clean_tex_log']=None
 checks['tex_log_note']='Not checked: compile the report first to generate its ignored build log.'
checks['slide_count']=len(p.slides)
source=root/'references/examples/stock-price-ga-lstm-presentation.pptx'
src=Presentation(source)
checks['original_slide_dimensions']=(p.slide_width,p.slide_height)==(src.slide_width,src.slide_height)
with zipfile.ZipFile(source) as z1,zipfile.ZipFile(deck) as z2:
 parts=[n for n in z1.namelist() if n.startswith('ppt/theme/') and n.endswith('.xml')]
 checks['original_theme_parts_byte_preserved']=all(z1.read(n)==z2.read(n) for n in parts)
checks['native_result_table_count']=sum(x.has_table for s in p.slides for x in s.shapes)
tables=[x.table for s in p.slides for x in s.shapes if x.has_table]
table=tables[0]
d=json.loads((root/'results/final/final_results.json').read_text())
expected=[]
for key in ['default_svr','random_search','de']:
 h=d['comparison'][key]['holdout']
 expected.append([f'{h[k]:.4f}' if key=='default_svr' else f"{h[k]['mean']:.4f} ± {h[k]['std']:.4f}" for k in ['rmse','mae','r2']])
checks['ppt_table_matches_frozen_json']=all(table.cell(i+1,j+1).text==expected[i][j] for i in range(3) for j in range(3))
ext=json.loads((root/'results/extension/extension_results.json').read_text())
ea={(a['feature_set'],a['method']):a for a in ext['aggregates']}
et=tables[1]
checks['ppt_extension_table_matches_extension_json']=(et.cell(1,2).text==f"{ext['default_svr']['log_age']['holdout_metrics']['rmse']:.4f}" and et.cell(2,2).text==f"{ea['log_age','RandomSearch']['holdout_rmse']['mean']:.4f} ± {ea['log_age','RandomSearch']['holdout_rmse']['std']:.4f}" and et.cell(3,2).text==f"{ea['log_age','rand/1/bin']['holdout_rmse']['mean']:.4f} ± {ea['log_age','rand/1/bin']['holdout_rmse']['std']:.4f}")
receipt=json.loads((root/'docs/validation/presentation-finalization.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
checks['ppt_matches_finalization_receipt']=sha(deck)==receipt['finalSha256']
checks['ppt_finalizer_no_findings_or_warnings']=receipt['presentationLayout']['findingCount']==0 and receipt['presentationLayout']['warning_count']==0 and receipt['packageIntegrity']['findingCount']==0
checks['report_sha256']=sha(report);checks['pptx_sha256']=sha(deck)
checks['validation_scope']='Automated artifact checks; visual review is recorded separately in docs/deliverable-validation.md.'
checks['artifact_import_limitation']='Bundled Artifact Tool import lacked @oai/granola/node; used targeted python-pptx edits and first-party package/layout/font finalization. Import check skipped explicitly.'
failed=[k for k,v in checks.items() if v is False]
checks['status']='pass' if not failed else 'fail';checks['failed_checks']=failed
print(json.dumps(checks,indent=2))
if failed:raise SystemExit(1)
