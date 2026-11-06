# /// script
# requires-python = ">=3.11"
# dependencies = ["python-pptx==1.0.2"]
# ///
"""Adapt the supplied BMSCE PPTX in place at the object level; preserve its theme."""
from pathlib import Path
from copy import deepcopy
import json
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'references/examples/stock-price-ga-lstm-presentation.pptx'
OUT=ROOT/'presentation'
P=Presentation(SOURCE)
BLUE=RGBColor(0,35,110)

def text(shape,content,size=36,align=PP_ALIGN.LEFT,bold=False,color=None):
 tf=shape.text_frame;tf.clear();tf.word_wrap=True
 tf.margin_left=Inches(.12);tf.margin_right=Inches(.12)
 tf.margin_top=Inches(.05);tf.margin_bottom=Inches(.05)
 for i,line in enumerate(content.split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
  p.alignment=align;p.space_after=Pt(12);p.space_before=Pt(0)
  p.font.name='Times New Roman';p.font.size=Pt(size);p.font.bold=bold
  if color: p.font.color.rgb=color
  # Keep paragraphs flat and editable; discard inherited bullet markers.
  pp=p._p.get_or_add_pPr()
  for tag in ['a:buChar','a:buAutoNum','a:buBlip']:
   for node in pp.findall(tag,pp.nsmap): pp.remove(node)
  pp.append(OxmlElement('a:buNone'))
  p.text=line
 return shape

def box(s,x,y,w,h,content,size=36,align=PP_ALIGN.LEFT,bold=False,color=None):
 return text(s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)),content,size,align,bold,color)

def clear_content(s):
 # Preserve institutional chrome, original master, logo and theme.
 for j in range(len(s.shapes)-1,7,-1):
  el=s.shapes[j]._element;el.getparent().remove(el)
 if len(s.shapes)>4 and s.shapes[4].has_text_frame:text(s.shapes[4],'')

def title(s,t):
 sh=s.shapes[1];sh.left=Inches(4.3);sh.width=Inches(17);sh.top=Inches(.36);sh.height=Inches(.85)
 text(sh,t,46,PP_ALIGN.CENTER,bold=True,color=BLUE)

def body(s,t):
 clear_content(s);box(s,1.2,1.9,19.7,9,t,36)

def notes(s,t):s.notes_slide.notes_text_frame.text=t

def clone(src):
 s=P.slides.add_slide(src.slide_layout)
 for sh in list(s.shapes):sh._element.getparent().remove(sh._element)
 mapping={}
 for rel in src.part.rels.values():
  if rel.reltype.endswith('/slideLayout') or rel.reltype.endswith('/notesSlide'):continue
  mapping[rel.rId]=s.part.relate_to(rel.target_ref if rel.is_external else rel.target_part,rel.reltype,rel.is_external)
 for sh in src.shapes:
  node=deepcopy(sh._element)
  for el in node.iter():
   for k,v in list(el.attrib.items()):
    if k.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}') and v in mapping:el.set(k,mapping[v])
  s.shapes._spTree.insert_element_before(node,'p:extLst')
 return s

original=list(P.slides)
arch=clone(original[2]);deflow=clone(original[2]);space=clone(original[2]);ext_table=clone(original[2]);ext_chart=clone(original[2]);ext_var=clone(original[2])
classification=clone(original[2]);algorithm=clone(original[2]);convergence=clone(original[2]);residual=clone(original[2]);learning=clone(original[2]);future=clone(original[2]);refs=clone(original[2])
order=[original[0],original[1],original[2],original[3],classification,original[4],original[5],original[6],algorithm,original[7],convergence,residual,learning,original[8],original[9],future,refs,original[10]]
final_order=[original[0],original[1],original[2],original[3],classification,original[4],original[5],arch,original[6],algorithm,deflow,original[7],convergence,space,residual,learning,ext_table,ext_chart,ext_var,original[8],original[9],future,refs,original[10]]
ids={id(P.part.related_slide(x.rId)):deepcopy(x) for x in P.slides._sldIdLst}
for node in list(P.slides._sldIdLst):P.slides._sldIdLst.remove(node)
for s in final_order:P.slides._sldIdLst.append(ids[id(s)])
for i,s in enumerate(P.slides):
 # Replace original page marker and make the footer fit within the slide.
 for sh in s.shapes:
  if not sh.has_text_frame:continue
  if '‹#›' in sh.text:text(sh,str(i+1),16,PP_ALIGN.RIGHT)
  if 'Department of Computer Science Engineering' in sh.text:
   sh.left=Inches(5);sh.width=Inches(12);text(sh,'Department of CSE (Data Science) | AY 2026–27',16,PP_ALIGN.CENTER)
 notes(s,'Concrete Strength DE–SVR. Evidence: docs/technical-closeout.md and results/final/final_results.json. All tuned aggregates are five optimizer seeds on one fixed holdout. No significant superiority over Random Search is claimed.')
# Cover uses the original background, triangle, logo, college label and layout.
s=original[0]
sh=s.shapes[5];sh.left=Inches(4.5);sh.top=Inches(1.4);sh.width=Inches(16.3);sh.height=Inches(3.9)
text(sh,'Bio-inspired Algorithms | 23DS7BSBIO\n\nConcrete Compressive Strength Prediction\nUsing Differential Evolution–Optimized\nSupport Vector Regression',38,PP_ALIGN.CENTER,bold=True)
sh=s.shapes[1];sh.left=Inches(5.7);sh.top=Inches(5.4);sh.width=Inches(14.8);sh.height=Inches(6.2)
text(sh,'R V Abhishek (1BM23CD047) • Sushanth S (1BM23CD063)\nUllas N (1BM23CD067) • Vedantha V V (1BM23CD069)\n\nGuide: Prof. Manoj Kumar, Assistant Professor\nHOD: Dr. Shyamala G\nDepartment of CSE (Data Science), BMSCE\nAY 2026–27',30,PP_ALIGN.CENTER)
# Clean the decorative empty object that protrudes beyond the cover.
for sh in list(s.shapes):
 if sh.left<0:sh.left=0
 if sh.width>P.slide_width:sh.width=P.slide_width
 if sh.left+sh.width>P.slide_width:sh.width=P.slide_width-sh.left
s=original[1];title(s,'Table of Contents');text(s.shapes[4],'Introduction to Optimization Problems\nWhat are Nature-Inspired Algorithms?\nClassification of Nature-Inspired Algorithms\nProblem Statement and Dataset\nImplementation and Results\nPerformance Metrics and Benchmarking\nAdvantages and Limitations\nFuture Scope and References',36)
s=original[2];title(s,'Introduction to Optimization Problems');body(s,'Optimization selects parameters that minimize an objective.\nHere: minimize five-fold development RMSE of an RBF-SVR.\nDecision variables: log₁₀(C), log₁₀(γ), log₁₀(ε).\nConstraints: fixed parameter bounds and 300 objective calls.\nThe objective is evaluated by fitting models; derivatives are unavailable.\nHoldout performance evaluates fixed selections after tuning.')
s=original[3];title(s,'What are Nature-Inspired Algorithms?');body(s,'Search methods motivated by biological, collective or physical processes.\nThey explore candidate solutions and use measured fitness to guide updates.\nGenetic Algorithm: selection, crossover and mutation.\nDifferential Evolution: mutation from population-vector differences.\nParticle Swarm Optimization: individual and social search information.\nNo gradient is required; performance still depends on task and controls.')
s=classification;title(s,'Classification of Nature-Inspired Algorithms');body(s,'Evolutionary methods: Genetic Algorithms and Differential Evolution.\nSwarm methods: Particle Swarm Optimization and Ant Colony Optimization.\nPhysical-process methods: Simulated Annealing.\nThis project implements DE/rand/1/bin for continuous parameters.\nRandom Search is the equally budgeted tuning comparator.\nThe other algorithms are background methods, not measured baselines.')
s=original[4];title(s,'Problem Statement');body(s,'Predict concrete compressive strength in MPa from ingredients and age.\nSVR accuracy depends on regularization C, kernel γ and tolerance ε.\nQuestion: does DE improve tuning under an equal evaluation budget?\nCompare default SVR, Random Search–SVR and DE–SVR.\nKeep data splits, preprocessing, search bounds and budgets fixed.\nReport all predefined seeds and the limits of the comparison.')
s=original[5];title(s,'Dataset and Preprocessing');body(s,'UCI Concrete Compressive Strength: 1,030 rows and eight inputs.\nSeven ingredient quantities (kg/m³) and curing age (days).\nTarget: compressive strength (MPa); no missing values.\n996 unique input tuples; identical inputs stay in the same group.\nDevelopment: 826 rows / 796 groups. Holdout: 204 rows / 200 groups.\nFive group-disjoint CV folds; StandardScaler fitted within each fold.\nFrozen runs use original features; the extension uses ln(age). All rows kept.')
s=original[6];title(s,'Implementation and Results');clear_content(s)
box(s,1.2,1.9,9.4,8.8,'Pipeline\nRaw-data audit and saved group splits\nStandardScaler → RBF-SVR\nDevelopment CV evaluates candidates\nRefit selected parameters on development\nEvaluate on fixed holdout\nSave histories, predictions and provenance',34)
box(s,11.4,1.9,9.5,8.8,'DE configuration\nPopulation: 15; F = 0.8; CR = 0.9\n300 calls including initialization\n19 trial generations after initialization\nSeeds: 11, 22, 33, 44, 55\nlog₁₀ C: [−2, 4]; log₁₀ γ: [−5, 1]\nlog₁₀ ε: [−3, 1]',34)
s=algorithm;title(s,'Differential Evolution: Explicit Operators');body(s,'1. Initialize 15 candidates uniformly within the log bounds.\n2. Select three distinct donors, all excluding the current target.\n3. Mutate: v = xᵣ₁ + 0.8(xᵣ₂ − xᵣ₃); clip to bounds.\n4. Binomial crossover at 0.9; force one mutant coordinate.\n5. Evaluate trial using mean development CV RMSE.\n6. Accept trial when no worse; defer updates until generation end.\nStop after exactly 300 objective calls. No hidden polishing.')
s=original[7];title(s,'Performance Metrics and Benchmarking');clear_content(s)
box(s,1.2,1.7,19.7,1,'Same 204 holdout rows; tuned values are mean ± sample SD over five seeds.',30)
table=s.shapes.add_table(4,4, Inches(1.3), Inches(3.0), Inches(19.3), Inches(3.4)).table
for j,w in enumerate([7.5,4.5,4.3,3]):table.columns[j].width=Inches(w)
data=json.loads((ROOT/'results/final/final_results.json').read_text())
rows=[['Model','RMSE (MPa)','MAE (MPa)','R²']]
for key,label in [('default_svr','Default SVR'),('random_search','Random Search–SVR'),('de','DE–SVR')]:
 h=data['comparison'][key]['holdout']; vals=[f'{h[k]:.4f}' if key=='default_svr' else f"{h[k]['mean']:.4f} ± {h[k]['std']:.4f}" for k in ['rmse','mae','r2']];rows.append([label,*vals])
for i,row in enumerate(rows):
 for j,v in enumerate(row):
  cell=table.cell(i,j);cell.text=v;cell.vertical_anchor=MSO_ANCHOR.MIDDLE
  cell.fill.solid();cell.fill.fore_color.rgb=RGBColor(221,238,245) if i==0 else RGBColor(255,255,255)
  for p in cell.text_frame.paragraphs:p.font.name='Times New Roman';p.font.size=Pt(28);p.font.bold=i==0;p.font.color.rgb=RGBColor(0,0,0)
box(s,1.3,7.2,19.3,3,'DE reduces RMSE by about 37.2% relative to default SVR.\nDE and Random Search differ by only 0.0078 MPa (about 0.1%).\nConclusion: tuning helps; the two searches are essentially equivalent here.',34)

def plot(s,t,name,caption,folder='results/final'):
 title(s,t);clear_content(s)
 pic=s.shapes.add_picture(str(ROOT/folder/name), Inches(2), Inches(1.65),height=Inches(8.8))
 if pic.width>Inches(18):
  ratio=Inches(18)/pic.width;pic.width=Inches(18);pic.height=int(pic.height*ratio)
 pic.left=int((P.slide_width-pic.width)/2)
 box(s,1.2,10.5,19.7,.7,caption,24,PP_ALIGN.CENTER)
plot(convergence,'Development Validation Convergence','convergence.png','Equal budgets: 300 calls per method per seed, including initialization.')
plot(residual,'Predictions and Residuals','prediction_residuals.png','Demonstration: DE seed 11, chosen by validation; holdout RMSE 6.3712 MPa.')
plot(learning,'Learning-Curve Diagnostic','learning_curve.png','Three development-only folds; nested whole groups; fixed parameters; no retuning.')
ext=json.loads((ROOT/'results/extension/extension_results.json').read_text())
frozen=data['comparison']
agg={(a['feature_set'],a['method']):a for a in ext['aggregates']}
def pm(a,k):return f"{a[k]['mean']:.4f} ± {a[k]['std']:.4f}"
plot(arch,'System Architecture: Data to Evidence','architecture.png','Four stages: data, splits and features, development-only optimisation, single holdout evaluation.','report/assets')
plot(deflow,'DE Flowchart (as Implemented)','de-flowchart.png','Frozen-generation donors, clipping, forced crossover coordinate, greedy selection, 300-call budget.','report/assets')
box(deflow,0.9,2.6,7,7,'Per generation\n15 trial candidates\nDonors from the frozen generation\nGreedy acceptance: trial ≤ target',30)
box(deflow,14.4,2.6,7,7,'Budget\n15 initial calls\n19 generations × 15 trials\n= 300 calls per seed',30)
plot(space,'Where Each Search Evaluated Candidates','search_space.png','1,500 candidates per method (5 seeds): DE concentrates in the good region; Random Search stays uniform.','report/assets')
title(ext_table,'Extension: ln(age) Input for All Three Methods');clear_content(ext_table)
box(ext_table,1.2,1.7,19.7,1,'Same 204 holdout rows; tuned values are mean ± sample SD over five seeds.',30)
t2=ext_table.shapes.add_table(4,4,Inches(1.3),Inches(2.9),Inches(19.3),Inches(3.4)).table
for j,w in enumerate([6.5,4.4,4.4,4.0]):t2.columns[j].width=Inches(w)
ln={'Default SVR':(frozen['default_svr']['holdout']['rmse'],ext['default_svr']['log_age']['holdout_metrics']),'Random Search–SVR':(frozen['random_search']['holdout']['rmse']['mean'],agg['log_age','RandomSearch']),'DE–SVR':(frozen['de']['holdout']['rmse']['mean'],agg['log_age','rand/1/bin'])}
rows2=[['Model','Raw RMSE (MPa)','ln(age) RMSE (MPa)','ln(age) R²']]
for label,(raw_rmse,new) in ln.items():
 if label=='Default SVR':rows2.append([label,f'{raw_rmse:.4f}',f"{new['rmse']:.4f}",f"{new['r2']:.4f}"])
 else:rows2.append([label,f'{raw_rmse:.4f}',pm(new,'holdout_rmse'),f"{new['holdout_r2']['mean']:.4f}"])
for i,row in enumerate(rows2):
 for j,v in enumerate(row):
  cell=t2.cell(i,j);cell.text=v;cell.vertical_anchor=MSO_ANCHOR.MIDDLE
  cell.fill.solid();cell.fill.fore_color.rgb=RGBColor(221,238,245) if i==0 else RGBColor(255,255,255)
  for para in cell.text_frame.paragraphs:para.font.name='Times New Roman';para.font.size=Pt(26);para.font.bold=i==0;para.font.color.rgb=RGBColor(0,0,0)
de_n=agg['log_age','rand/1/bin']['holdout_rmse']['mean'];rs_n=agg['log_age','RandomSearch']['holdout_rmse']['mean'];de_o=frozen['de']['holdout']['rmse']['mean']
box(ext_table,1.3,6.9,19.3,4,f"Representation drives the gain: DE {de_o:.2f} → {de_n:.2f} MPa ({100*(de_o-de_n)/de_o:.1f}% lower).\nDE vs Random Search on ln(age): {abs(rs_n-de_n):.3f} MPa apart; no significance claim.\nln(age) chosen after a development-only probe; holdout was inspected in Stage 1.",32)
plot(ext_chart,'Representation Comparison','representation_comparison.png','Holdout RMSE, mean ± SD over five optimizer seeds; raw rows are the frozen results.','report/assets')
plot(ext_var,'DE Variant Ablation (ln(age))','de_variants.png','Same 300-call budget; rand/1/bin vs current-to-best/1/bin vs jDE vs Random Search.','report/assets')
s=original[8];title(s,'Advantages');body(s,'Explicit, tested DE operators for a three-parameter continuous search.\nBoth tuned methods substantially improve default SVR.\nGroup-aware splits and fold-local scaling reduce leakage risks.\nEqual candidate budgets make the search comparison auditable.\nComplete histories, predictions and locked dependencies support reproduction.\nForty-three tests and a saved evidence audit support technical closeout.')
s=original[9];title(s,'Limitations');body(s,'One public dataset and one fixed development / holdout partition.\nSeed SD describes optimizer variability, not independent dataset uncertainty.\nDE does not show meaningful superiority over equally budgeted Random Search.\nBaseline and Random Search holdout evaluations preceded final DE evaluation.\nNo feature-importance or formal significance study; ln(age) was motivated by a development probe.\nFinite search cannot prove global optimality; no field deployment is validated.')
s=future;title(s,'Future Scope');body(s,'Evaluate on external laboratory data using a frozen model.\nUse repeated outer group splits or nested group cross-validation.\nTest DE control settings systematically under matched budgets.\nStudy uncertainty and age-stratified errors with a declared protocol.\nAdd interpretation studies without using holdout feedback for tuning.\nAssess material or environmental benefits only with suitable new evidence.')
s=refs;title(s,'References');body(s,'[1] I.-C. Yeh, Concrete Compressive Strength, UCI, 1998.\n      Dataset DOI: 10.24432/C5PK67.\n[2] I.-C. Yeh, Cement and Concrete Research, 28(12), 1797–1808, 1998.\n[3] R. Storn and K. Price, Journal of Global Optimization, 11, 341–359, 1997.\n[4] J. Bergstra and Y. Bengio, JMLR, 13, 281–305, 2012.\n[5] A. J. Smola and B. Schölkopf, Statistics and Computing, 14, 199–222, 2004.\n[6] scikit-learn documentation: SVR, StandardScaler and GroupKFold.')
notes(refs,'Sources: https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength ; https://doi.org/10.1016/S0008-8846(98)00165-3 ; https://doi.org/10.1023/A:1008202821328 ; https://www.jmlr.org/papers/v13/bergstra12a.html ; https://doi.org/10.1023/B:STCO.0000035301.49549.88 ; https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html')
s=original[10]
# Thank-you original uses a different shape index arrangement.
for sh in s.shapes:
 if sh.has_text_frame and 'THANK YOU' in sh.text:text(sh,'THANK YOU',48,PP_ALIGN.CENTER,color=BLUE)
box(s,2,8.5,18,1.5,'Both tuned methods improve default SVR.\nDE and Random Search perform essentially equivalently.',34,PP_ALIGN.CENTER)
box(s,1.5,10.2,19,.7,'github.com/R-V-Abhishek/concrete-strength-de-svr',26,PP_ALIGN.CENTER)
P.core_properties.title='Concrete Compressive Strength Prediction Using DE–SVR'
P.core_properties.author='R V Abhishek; Sushanth S; Ullas N; Vedantha V V'
P.core_properties.subject='Bio-inspired Algorithms AAT, 23DS7BSBIO, AY 2026–27'
P.core_properties.comments='Adapted from the supplied BMSCE presentation; original reference retained.'
# Strengthen hierarchy within the supplied layout, preserving its visual identity.
section_labels={2:'Objective and search space',3:'Nature-inspired search',4:'Algorithm families',5:'Prediction task',6:'Dataset and evaluation split',8:'DE/rand/1/bin',13:'What this approach offers',14:'What the evidence cannot establish',15:'Next experiments',16:'Selected sources'}
for idx,label in section_labels.items():
 s=order[idx]
 for sh in s.shapes:
  if sh.has_text_frame and sh.top>=Inches(1.8) and sh.top<Inches(10.5) and sh.text:
   sh.top=Inches(2.65);sh.height=Inches(7.9)
   for para in sh.text_frame.paragraphs:
    para.font.size=Pt(36);para.space_after=Pt(23)
   if idx==16:
    for para in sh.text_frame.paragraphs:para.font.size=Pt(32);para.space_after=Pt(14)
 box(s,1.2,1.75,19.7,.75,label,39,bold=True,color=BLUE)
for sh in original[6].shapes:
 if sh.has_text_frame and sh.top>Inches(1.5) and sh.top<Inches(3):
  para=sh.text_frame.paragraphs[0];para.font.size=Pt(40);para.font.bold=True;para.font.color.rgb=BLUE
for j in range(4):
 cell=table.cell(3,j)
 for para in cell.text_frame.paragraphs:para.font.bold=True;para.font.color.rgb=BLUE
# Source background rectangles overshoot by a few points; fit them to the canvas.
for s in P.slides:
 bg=s.shapes[0]
 bg.left=0;bg.top=0;bg.width=P.slide_width;bg.height=P.slide_height
P.save(OUT/'concrete-strength-de-svr-presentation.pptx')
# Reusable PowerPoint: same exact masters, slide size, theme and institutional chrome.
T=Presentation(OUT/'concrete-strength-de-svr-presentation.pptx')
text(T.slides[0].shapes[5],'[Course Name] | [Course Code]\n\n[Project Title]\n[Project Subtitle]',38,PP_ALIGN.CENTER,bold=True)
text(T.slides[0].shapes[1],'[Student One (USN)] • [Student Two (USN)]\n[Student Three (USN)] • [Student Four (USN)]\n\nGuide: [Name], [Designation]\nHOD: [Name]\nDepartment of CSE (Data Science), BMSCE\nAY [Academic Year]',30,PP_ALIGN.CENTER)
for i,s in enumerate(T.slides):
 for sh in s.shapes:
  if sh.has_table:
   for row in sh.table.rows:
    for cell in row.cells:cell.text='[Value]'
  elif sh.has_text_frame:
   if sh==s.shapes[1] and i>0:continue
   if i==0:continue
   elif i>0 and sh.top>Inches(1.5) and sh.top<Inches(11.3):text(sh,'[Replace with project-specific content and evidence]',32)
   elif 'AY 2026' in sh.text:text(sh,'Department of CSE (Data Science) | [Academic Year]',16,PP_ALIGN.CENTER)
  elif sh.shape_type==13 and sh.top>Inches(1.5):
   el=sh._element;el.getparent().remove(el)
 notes(s,'Reusable BMSCE template. Replace topic-specific headings, all placeholders, evidence and notes before submission. Preserve institutional branding; confirm current faculty and academic details.')
T.core_properties.title='BMSCE Academic Presentation Template';T.core_properties.author='BMSCE Academic Templates';T.core_properties.subject='Reusable project presentation'
T.save(OUT/'bmsce-presentation-template.pptx')
print(f'Wrote {len(P.slides)} project slides and reusable presentation template.')
