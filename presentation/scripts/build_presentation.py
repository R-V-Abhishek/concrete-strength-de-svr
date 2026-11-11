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


LIGHT=RGBColor(221,238,245)
from pptx.enum.shapes import MSO_SHAPE
def bullets(s,items,x=1.2,y=2.75,w=13.4,h=8.3,size=34,numbered=False,gap=18):
 """Real bullets (or numbers) with a bold navy lead-in per item; editable text."""
 tb=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=tb.text_frame;tf.word_wrap=True
 tf.margin_left=Inches(.12);tf.margin_right=Inches(.12);tf.margin_top=Inches(.05);tf.margin_bottom=Inches(.05)
 for i,(lead,rest) in enumerate(items):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
  p.space_after=Pt(gap);p.space_before=Pt(0);p.alignment=PP_ALIGN.LEFT
  pp=p._p.get_or_add_pPr();pp.set('marL',str(int(Inches(.55))));pp.set('indent',str(-int(Inches(.55))))
  clr=OxmlElement('a:buClr');rgb=OxmlElement('a:srgbClr');rgb.set('val','00236E');clr.append(rgb);pp.append(clr)
  if numbered:
   bu=OxmlElement('a:buFont');bu.set('typeface','Times New Roman');pp.append(bu)
   bu=OxmlElement('a:buAutoNum');bu.set('type','arabicPeriod');pp.append(bu)
  else:
   bu=OxmlElement('a:buFont');bu.set('typeface','Arial');pp.append(bu)
   bu=OxmlElement('a:buChar');bu.set('char','•');pp.append(bu)
  if lead:
   r=p.add_run();r.text=lead+' ';r.font.name='Times New Roman';r.font.size=Pt(size);r.font.bold=True;r.font.color.rgb=BLUE
  r=p.add_run();r.text=rest;r.font.name='Times New Roman';r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
 return tb
def card(s,x,y,w,h,value,label,vsize=36,lsize=24):
 sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 sh.adjustments[0]=.12;sh.fill.solid();sh.fill.fore_color.rgb=LIGHT;sh.line.fill.background();sh.shadow.inherit=False
 tf=sh.text_frame;tf.word_wrap=True;tf.vertical_anchor=MSO_ANCHOR.MIDDLE
 tf.margin_left=tf.margin_right=Inches(.1);tf.margin_top=tf.margin_bottom=Inches(.04)
 for j,(t_,sz,b,c) in enumerate([(value,vsize,True,BLUE),(label,lsize,False,RGBColor(0,0,0))]):
  p=tf.paragraphs[0] if j==0 else tf.add_paragraph();p.alignment=PP_ALIGN.CENTER;p.space_after=Pt(0)
  r=p.add_run();r.text=t_;r.font.name='Times New Roman';r.font.size=Pt(sz);r.font.bold=b;r.font.color.rgb=c
 return sh
def cards(s,items,x=15.2,y=3.45,w=6.3,cols=1,h=2.2,gap=.3,vsize=48,lsize=24):
 cw=(w-gap*(cols-1))/cols
 for k,(v,l) in enumerate(items):
  card(s,x+(k%cols)*(cw+gap),y+(k//cols)*(h+gap),cw,h,v,l,vsize,lsize)
def panel(s,title_text,label,items,stats,glance='At a glance',cols=1,numbered=False,size=34,bw=13.4,h=2.2,vsize=48):
 """Common content pattern: heading, bulleted text on the left, key data cards on the right."""
 title(s,title_text);clear_content(s)
 box(s,1.2,1.75,13.4,.75,label,39,bold=True,color=BLUE)
 box(s,15.2,1.75,6.3,.75,glance,39,bold=True,color=BLUE)
 bullets(s,items,w=bw,size=size,numbered=numbered);cards(s,stats,cols=cols,h=h,vsize=vsize)
def link_lines(s,items,x,y,w,h,size):
 tb=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=tb.text_frame;tf.word_wrap=True
 for i,(t_,url) in enumerate(items):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.space_after=Pt(12)
  r=p.add_run();r.text=t_;r.font.name='Times New Roman';r.font.size=Pt(size);r.hyperlink.address=url
 return tb

original=list(P.slides)
arch=clone(original[2]);deflow=clone(original[2]);space=clone(original[2]);ext_table=clone(original[2]);ext_chart=clone(original[2]);ext_var=clone(original[2])
classification=clone(original[2]);algorithm=clone(original[2]);convergence=clone(original[2]);residual=clone(original[2]);learning=clone(original[2]);future=clone(original[2]);refs=clone(original[2])
objectives=clone(original[2]);ard=clone(original[2]);rep=clone(original[2]);findings=clone(original[2])
intro,nia,problem,dataset,impl,metrics,adv,lim,thanks=original[2],original[3],original[4],original[5],original[6],original[7],original[8],original[9],original[10]
final_order=[original[0],original[1],intro,nia,classification,problem,objectives,dataset,arch,impl,algorithm,deflow,metrics,convergence,space,residual,learning,ext_table,ext_chart,ext_var,ard,rep,findings,adv,lim,future,refs,thanks]
# Sections drive the agenda, footer tags and slide-number ranges, so they cannot drift from the deck order.
SECTIONS=[('Background','Optimization problems, nature-inspired algorithms, classification',[intro,nia,classification]),
('Problem and Method','Problem statement, objectives, dataset, architecture, implementation, DE operators',[problem,objectives,dataset,arch,impl,algorithm,deflow]),
('Results','Performance metrics and benchmarking, convergence, search space, predictions, learning curve',[metrics,convergence,space,residual,learning]),
('Extensions','ln(age) representation, DE variants, ARD kernel, replication on new splits',[ext_table,ext_chart,ext_var,ard,rep]),
('Conclusions','Key findings, advantages, limitations, future scope, references',[findings,adv,lim,future,refs])]
section_of={id(s):(k+1,name) for k,(name,_,ss) in enumerate(SECTIONS) for s in ss}
NSLIDES=len(final_order)
ids={id(P.part.related_slide(x.rId)):deepcopy(x) for x in P.slides._sldIdLst}
for node in list(P.slides._sldIdLst):P.slides._sldIdLst.remove(node)
for s in final_order:P.slides._sldIdLst.append(ids[id(s)])
for i,s in enumerate(P.slides):
 # Replace original page marker and make the footer fit within the slide.
 for sh in s.shapes:
  if not sh.has_text_frame:continue
  if '‹#›' in sh.text:text(sh,f'{i+1} / {NSLIDES}',16,PP_ALIGN.RIGHT);sh.left=Inches(18.2);sh.width=Inches(3.4)
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
s=original[1];title(s,'Table of Contents');clear_content(s)
pos={id(x):n+1 for n,x in enumerate(final_order)}
box(s,1.2,1.9,2,.8,'No.',30,bold=True,color=BLUE);box(s,3.2,1.9,15,.8,'Section and topics',30,bold=True,color=BLUE);box(s,18.2,1.9,3.4,.8,'Slides',30,bold=True,color=BLUE)
for k,(name,topics,ss) in enumerate(SECTIONS):
 y=2.9+k*1.55;a,b=pos[id(ss[0])],pos[id(ss[-1])]
 box(s,1.2,y,2,.7,str(k+1),34,bold=True,color=BLUE);box(s,3.2,y,15,.7,name,34,bold=True)
 box(s,3.2,y+.62,15,.7,topics,22);box(s,18.2,y,3.4,.7,f'{a}–{b}',34)
panel(original[2],'Introduction to Optimization Problems','Objective and search space',[('Objective:','minimize the five-fold development RMSE of an RBF-SVR.'),('Decision variables:','log₁₀ C, log₁₀ γ and log₁₀ ε.'),('Constraints:','fixed parameter bounds and a budget of 300 objective calls.'),('Evaluation:','every candidate means fitting models; no derivatives are available.'),('Holdout:','used only to score fixed selections after tuning.')],[('3','decision variables'),('300','objective calls per run'),('5','CV folds per evaluation')])
panel(original[3],'What are Nature-Inspired Algorithms?','Nature-inspired search',[('Idea:','search methods motivated by biological, collective or physical processes.'),('Mechanism:','explore candidate solutions; measured fitness guides the updates.'),('Genetic Algorithm:','selection, crossover and mutation.'),('Differential Evolution:','mutation from population-vector differences.'),('Particle Swarm:','individual and social search information.'),('Caveat:','no gradient is required, but performance depends on task and controls.')],[('0','gradients required'),('1','method implemented: DE'),('3','models compared')])
panel(classification,'Classification of Nature-Inspired Algorithms','Algorithm families',[('Evolutionary:','Genetic Algorithms and Differential Evolution.'),('Swarm:','Particle Swarm Optimization and Ant Colony Optimization.'),('Physical process:','Simulated Annealing.'),('Implemented:','DE/rand/1/bin for continuous parameters.'),('Comparator:','Random Search with an equal tuning budget.'),('Background only:','the other algorithms are not measured baselines.')],[('3','families covered'),('1','implemented: DE/rand/1/bin'),('1','comparator: Random Search')])
panel(original[4],'Problem Statement','Prediction task',[('Task:','predict concrete compressive strength (MPa) from ingredients and age.'),('Difficulty:','SVR accuracy depends on C, kernel γ and tolerance ε.'),('Question:','does DE improve tuning under an equal evaluation budget?'),('Comparison:','default SVR, Random Search–SVR and DE–SVR.'),('Controls:','splits, preprocessing, bounds and budgets stay fixed.'),('Reporting:','all predefined seeds and the limits of the comparison.')],[('8','input features'),('1','target: strength (MPa)'),('3','models compared')])
panel(original[5],'Dataset and Preprocessing','Dataset and evaluation split',[('Source:','UCI Concrete Compressive Strength; no missing values.'),('Inputs:','seven ingredient quantities (kg/m³) and curing age (days).'),('Target:','compressive strength (MPa).'),('Grouping:','996 unique input tuples; identical inputs share a group.'),('Validation:','five group-disjoint CV folds; StandardScaler fitted within each fold.'),('Features:','frozen runs use the original inputs; Extension 1 adds ln(age).')],[('1,030','rows'),('8','input features'),('826 / 204','development / holdout rows'),('796 / 200','development / holdout groups')],cols=2,h=2.6,vsize=40)
panel(original[6],'Implementation and Results','Pipeline',[('Data:','raw-data audit and saved group splits.'),('Model:','StandardScaler → RBF-SVR.'),('Search:','development CV evaluates every candidate.'),('Refit:','selected parameters refit on all development rows.'),('Evaluate:','fixed holdout scored once.'),('Save:','histories, predictions and provenance.')],[('15','population'),('0.8 / 0.9','F / CR'),('300','calls incl. initialization'),('19','trial generations'),('5','optimizer seeds'),('[−2, 4]','log₁₀ C bounds'),('[−5, 1]','log₁₀ γ bounds'),('[−3, 1]','log₁₀ ε bounds')],glance='DE configuration',cols=2,h=1.7,vsize=34,size=32)
panel(algorithm,'Differential Evolution: Explicit Operators','DE/rand/1/bin',[('Initialize:','15 candidates uniformly within the log bounds.'),('Donors:','three distinct vectors, all excluding the current target.'),('Mutate:','v = xᵣ₁ + 0.8(xᵣ₂ − xᵣ₃), clipped to bounds.'),('Crossover:','binomial at 0.9; one mutant coordinate is forced.'),('Evaluate:','mean development CV RMSE of the trial.'),('Select:','keep the trial if no worse; updates deferred to generation end.'),('Stop:','after exactly 300 objective calls; no hidden polishing.')],[('F = 0.8','mutation weight'),('CR = 0.9','crossover rate'),('15','population size'),('300','objective calls per seed')],glance='Settings',numbered=True,size=30,h=1.75,vsize=40)
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
bullets(s,[('Improvement:','DE reduces RMSE by about 37.2% relative to default SVR.'),('Gap:','DE and Random Search differ by only 0.0078 MPa (about 0.1%).'),('Conclusion:','tuning helps; the two searches are essentially equivalent here.')],x=1.3,y=7.1,w=19.3,h=3.8,size=34)

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
title(deflow,'DE Flowchart (as Implemented)');clear_content(deflow)
deflow.shapes.add_picture(str(ROOT/'report/assets/de-flowchart-wide.png'),Inches(.9),Inches(2.1),width=Inches(20.2))
for k,(v,l) in enumerate([('Per generation','15 trial candidates; donors from the frozen generation'),('Acceptance','greedy: trial replaces target if no worse'),('Budget','15 + 19 generations × 15 trials = 300 calls per seed')]):card(deflow,1.0+k*6.9,8.0,6.5,2.6,v,l,36,26)
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
bullets(ext_table,[('Representation:',f'DE {de_o:.3f} → {de_n:.3f} MPa ({100*(de_o-de_n)/de_o:.1f}% lower).'),('DE vs Random Search:',f'{abs(rs_n-de_n):.3f} MPa apart on ln(age); no significance claim.'),('Disclosure:','ln(age) was chosen after a development-only probe; the holdout was inspected in Stage 1.')],x=1.3,y=6.9,w=19.3,h=4,size=34)
plot(ext_chart,'Representation Comparison','representation_comparison.png','Holdout RMSE, mean ± SD over five optimizer seeds; raw rows are the frozen results.','report/assets')
plot(ext_var,'DE Variant Ablation (ln(age))','de_variants.png','Same 300-call budget; rand/1/bin vs current-to-best/1/bin vs jDE vs Random Search.','report/assets')
panel(objectives,'Objectives and Scope','Research questions',[('RQ1:','does tuning improve a default RBF-SVR? (frozen study)'),('RQ2:','does DE beat equally budgeted Random Search? (frozen study)'),('RQ3:','how much does the input representation matter? (Extension 1, ln(age))'),('RQ4:','does DE keep an edge in a 10-D search space and on new splits? (Extension 2)'),('Scope:','one UCI dataset, one RBF-SVR, explicit DE/rand/1/bin; extensions were pre-registered.')],[('4','research questions'),('2','pre-registered extensions'),('5','optimizer seeds')])
ard_res={(a['space'],a['method']):a for a in json.loads((ROOT/'results/extension2/ard_results.json').read_text())['aggregates']}
rep_all=json.loads((ROOT/'results/extension2/replication_results.json').read_text());rep_res=rep_all['summary']
rep_res['splits_de_better_validation']=sum(x['d_validation']>0 for x in rep_all['per_split'])+(rep_all['original_split']['d_validation']>0)
plot(ard,'Extension 2a: ARD Kernel (10-D Search Space)','ard_comparison.png','1,500 calls, five seeds; y-axis starts at 4.0 MPa. ARD does not improve validation RMSE over a shared γ.','report/assets')
plot(rep,'Extension 2b: Replication on Five New Splits','replication_gap.png',f"DE lower validation RMSE on {rep_res['splits_de_better_validation']}/{rep_res['splits_total']} splits, holdout on {rep_res['splits_de_better_holdout']}/{rep_res['splits_total']}; mean holdout gap {rep_res['all_splits_holdout']['mean']:.3f} MPa (indicative; splits overlap).",'report/assets')
panel(findings,'Key Findings','Summary of evidence',[('Tuning:',f"DE cuts holdout RMSE {100*(1-de_o/frozen['default_svr']['holdout']['rmse']):.1f}% ({frozen['default_svr']['holdout']['rmse']:.3f} → {de_o:.3f} MPa)."),('Frozen features:',f"DE and Random Search are {abs(frozen['random_search']['holdout']['rmse']['mean']-de_o):.4f} MPa apart."),('Representation:',f"ln(age) lowers DE to {de_n:.3f} MPa ({100*(de_o-de_n)/de_o:.1f}%), the largest effect."),('DE edge:',f"about {rep_res['all_splits_holdout']['mean']:.1f} MPa, on {rep_res['splits_de_better_holdout']} of {rep_res['splits_total']} splits; no significance claim."),('ARD (10-D):','no accuracy gain; Random Search degrades there, DE does not.')],[(f"{100*(1-de_o/frozen['default_svr']['holdout']['rmse']):.1f}%",'lower RMSE than default SVR'),(f"{100*(de_o-de_n)/de_o:.1f}%",'lower DE RMSE with ln(age)'),(f"≈{rep_res['all_splits_holdout']['mean']:.1f} MPa",'DE edge over Random Search'),(f"{rep_res['splits_de_better_holdout']} of {rep_res['splits_total']}",'splits favour DE on holdout')],glance='Key numbers',cols=2,h=2.6,vsize=36)
panel(adv,'Advantages','What this approach offers',[('Transparent search:','explicit, tested DE operators for a three-parameter continuous search.'),('Clear gain:','both tuned methods substantially improve default SVR.'),('Leakage control:','group-aware splits and fold-local scaling.'),('Auditable budget:','equal candidate budgets for every search.'),('Reproducible:','complete histories, predictions and locked dependencies.'),('Verified:','57 passing tests, checksummed evidence and a saved audit.')],[('57','passing tests'),('3','checksummed evidence sets'),('300','calls per search, equal'),('5','seeds per method')],glance='Evidence',cols=2,h=2.6,vsize=44)
panel(lim,'Limitations','What the evidence cannot establish',[('Data:','one public dataset; one main holdout (Extension 2 adds five overlapping splits).'),('Uncertainty:','seed SD shows optimizer variability, not dataset uncertainty.'),('DE vs Random Search:','no meaningful superiority is demonstrated.'),('Chronology:','baseline and Random Search holdout evaluations preceded final DE evaluation.'),('Analysis:','no feature-importance or significance study; ln(age) and ARD came from development probes.'),('Scope:','a finite search cannot prove global optimality; no field deployment is validated.')],[('1','dataset'),('204','main holdout rows'),('5','optimizer seeds'),('None','formal significance test')],glance='Scale of evidence',cols=2,h=2.6,vsize=44)
panel(future,'Future Scope','Next experiments',[('External data:','evaluate a frozen model on external laboratory data.'),('Splits:','non-overlapping outer splits or nested group cross-validation.'),('DE controls:','test settings systematically under matched budgets.'),('Uncertainty:','study age-stratified errors with a declared protocol.'),('Interpretation:','add studies without using holdout feedback for tuning.'),('Impact:','assess material or environmental benefits only with suitable new evidence.')],[('External','laboratory data'),('Nested','group cross-validation'),('Systematic','DE control study'),('Declared','protocol before evaluation')],glance='Priorities',cols=2,h=2.6,vsize=32)
title(refs,'References');clear_content(refs);box(refs,1.2,1.75,19.7,.75,'Selected sources (click to open)',39,bold=True,color=BLUE)
link_lines(refs,[('[1] I.-C. Yeh, Concrete Compressive Strength, UCI Machine Learning Repository, 1998.','https://doi.org/10.24432/C5PK67'),('[2] I.-C. Yeh, Cement and Concrete Research, 28(12), 1797–1808, 1998.','https://doi.org/10.1016/S0008-8846(98)00165-3'),('[3] R. Storn and K. Price, Journal of Global Optimization, 11, 341–359, 1997.','https://doi.org/10.1023/A:1008202821328'),('[4] J. Bergstra and Y. Bengio, JMLR, 13, 281–305, 2012.','https://www.jmlr.org/papers/v13/bergstra12a.html'),('[5] A. J. Smola and B. Schölkopf, Statistics and Computing, 14, 199–222, 2004.','https://doi.org/10.1023/B:STCO.0000035301.49549.88'),('[6] scikit-learn documentation: SVR, StandardScaler and GroupKFold.','https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html'),('[7] Project repository: code, results and report.','https://github.com/R-V-Abhishek/concrete-strength-de-svr')],1.2,2.75,19.7,8.3,28)
notes(refs,'Sources: https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength ; https://doi.org/10.1016/S0008-8846(98)00165-3 ; https://doi.org/10.1023/A:1008202821328 ; https://www.jmlr.org/papers/v13/bergstra12a.html ; https://doi.org/10.1023/B:STCO.0000035301.49549.88 ; https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html')
s=thanks;title(s,'Thank You')
for k,(v,l) in enumerate([('Tuning helps',f"DE cuts holdout RMSE {100*(1-de_o/frozen['default_svr']['holdout']['rmse']):.1f}% versus default SVR"),('Representation matters most',f"ln(age) lowers DE RMSE by {100*(de_o-de_n)/de_o:.1f}%"),('DE’s edge is small',f"about {rep_res['all_splits_holdout']['mean']:.1f} MPa; untested for significance")]):card(s,1.0+k*6.9,2.4,6.5,3.2,v,l,34,28)
box(s,1.2,6.5,19.6,1.1,'Questions and discussion',46,PP_ALIGN.CENTER,bold=True,color=BLUE)
box(s,1.2,7.9,19.6,1.4,'R V Abhishek • Sushanth S • Ullas N • Vedantha V V\nGuide: Prof. Manoj Kumar, Assistant Professor',26,PP_ALIGN.CENTER)
link_lines(s,[('github.com/R-V-Abhishek/concrete-strength-de-svr','https://github.com/R-V-Abhishek/concrete-strength-de-svr')],4,9.9,14,.8,28).text_frame.paragraphs[0].alignment=PP_ALIGN.CENTER
P.core_properties.title='Concrete Compressive Strength Prediction Using DE–SVR'
P.core_properties.author='R V Abhishek; Sushanth S; Ullas N; Vedantha V V'
P.core_properties.subject='Bio-inspired Algorithms AAT, 23DS7BSBIO, AY 2026–27'
P.core_properties.comments='Adapted from the supplied BMSCE presentation; original reference retained.'
# Strengthen hierarchy within the supplied layout, preserving its visual identity.
for j in range(4):
 cell=table.cell(3,j)
 for para in cell.text_frame.paragraphs:para.font.bold=True;para.font.color.rgb=BLUE
for s in final_order:
 if id(s) in section_of:
  k,name=section_of[id(s)];foot=[x for x in s.shapes if x.has_text_frame and 'AY 2026' in x.text][0]
  box(s,1.2,foot.top/914400,6.5,foot.height/914400,f'Section {k}: {name}',16,PP_ALIGN.LEFT,color=BLUE)
NOTES=['Introduce the project, the team and the guide. Frozen study plus two pre-registered extensions.',
'Five sections; slide ranges are computed from the deck order. All mandatory headings are covered.',
'Optimization framing: three log-scaled SVR parameters, 300 objective calls, no derivatives.',
'Nature-inspired search in general; DE is the one implemented method.',
'DE/rand/1/bin is the implemented method; Random Search is the measured comparator.',
'Problem: tune C, gamma and epsilon fairly under an equal budget. Source: docs/protocol.md.',
'Four research questions; RQ3 and RQ4 come from the extensions (docs/protocol-extension*.md).',
'UCI data, 1,030 rows; group-disjoint splits avoid repeated-tuple leakage. Source: data/processed/splits_manifest.json.',
'Four-stage architecture: data, splits and features, development-only optimisation, single holdout evaluation.',
'Pipeline and DE configuration. Source: configs/experiment.json and docs/protocol.md.',
'Explicit operators with deferred greedy selection; code in src/concrete_strength/de.py.',
'Flowchart as implemented; budget is 15 + 19 x 15 = 300 calls.',
'Frozen holdout metrics. Source: results/final/final_results.json. Mean and sample SD over five seeds.',
'Convergence on validation RMSE for all ten runs. Source: results/final/convergence.png.',
'Where each method sampled; DE concentrates in the good region. Source: report/assets/search_space.png.',
'Validation-selected demonstration, not an average. Source: results/final/prediction_residuals.png.',
'Development-only learning curve, three folds. Source: results/final/learning_curve.csv.',
'Extension 1 table. Source: results/extension/extension_results.json. ln(age) came from a development-only probe.',
'Representation comparison chart. Source: report/assets/representation_comparison.png.',
'DE variants and water ratios are indistinguishable within seed SD. Source: results/extension/.',
'Extension 2a: 1,500 calls. Random Search degrades in 10-D, DE does not, but ARD gives no accuracy gain. Source: results/extension2/ard_results.json.',
'Extension 2b: five new overlapping splits. Intervals are indicative only. Source: results/extension2/replication_results.json.',
'Summary of evidence; every number comes from the saved results.',
'Advantages of the approach and its evidence trail.',
'Limitations: single dataset, overlapping splits, no significance test, probe-motivated extensions.',
'Future scope: external data, nested CV, systematic DE controls.',
'Selected sources; full bibliography in the report.',
'Close with the two main messages and invite questions. Repository link on slide.']
assert len(NOTES)==NSLIDES
for s,n in zip(final_order,NOTES):notes(s,n)
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
