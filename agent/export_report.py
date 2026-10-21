import json, html, textwrap
from pathlib import Path
from collections import Counter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold',italic='DejaVu',boldItalic='DejaVu-Bold')
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
base=Path(__file__).parent; data=json.loads((base/'artifacts-final/results.json').read_text())
out=base.parents[1]/'output/qa-submission';out.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet()
for style in styles.byName.values(): style.fontName='DejaVu'
styles.add(ParagraphStyle(name='TitleQA',fontName='DejaVu-Bold',fontSize=29,leading=33,textColor=colors.HexColor('#132a45'),spaceAfter=16));styles.add(ParagraphStyle(name='SmallQA',fontName='DejaVu',fontSize=8,leading=11,spaceAfter=5));styles['BodyText'].spaceAfter=9;styles['BodyText'].leading=14
story=[]
def p(t,style='BodyText'):return Paragraph(html.escape(str(t)).replace('\n','<br/>'),styles[style])
def heading(t):story.append(p(t,'Heading2'))
def table(rows,widths):
 t=Table([[p(c,'SmallQA') for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef6')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d7dfe8'))]));story.append(t)
story += [p('SpecLens','TitleQA'),p('Autonomous specification-driven QA audit','Heading1'),p('CDF Agentic QA Hackathon | Raashid Shaik'),p('LOCAL DEMONSTRATION • '+data['run_utc'].replace('T',' ').split('.')[0]+' UTC','SmallQA')]
heading('Result at a glance');sc=data['scenario_counts'];rc=Counter(r['status'] for r in data['requirements'])
table([['Measure','Observed result'],['Browser scenarios',f"{sc.get('passed',0)} passed / {sc.get('failed',0)} failed / {sc.get('unverified',0)} unverified"],['PRD bullets',f"{rc['passed']} passed / {rc['failed']} failed / {rc['unverified']} unverified"],['Inference cost','$0.00; 0 remote model calls; 0 billed tokens'],['Run duration',str(data['runtime_seconds'])+' seconds']], [170,330])
heading('Scope and interpretation');story.append(p('This is a real browser run against the official local DemoBank target. The frontend and backend business logic and official seed are unchanged. PostgreSQL is supplied by PGlite 0.5.10 (WASM), with a serialized one-connection pool. These results do not establish the behavior of the organizer-hosted deployment or production PostgreSQL.'))
story.append(p('Requirement selection uses local TF-IDF and cosine-similarity NLP retrieval over PRD bullets and authored capability descriptions. Browser scenarios are authored DemoBank adapters. This is not an LLM-based or general-purpose web agent. Candidate similarity mappings never establish a pass; incomplete assertions remain unverified.'))
heading('Evidence and reproducibility');story.append(p('The supporting archive contains results.json, audit.html, per-scenario screenshots, visible page text, the PRD hash and run instructions. Failed scenarios below include expected versus observed values and steps. The walkthrough is a continuous browser recording, including a short agent-owned introduction, real execution, and the generated report.'))
story.append(p('Official starter commit: c7b856cc0d7cfb367e96fda0e5c291eba10cbb10','SmallQA'));story.append(p('PRD SHA-256: '+data['prd_sha256'],'SmallQA'))
for r in data['scenarios']:
 if r['verdict']!='failed':continue
 story.append(PageBreak());story.append(p(r['id']+' | '+r['name'],'Heading1'))
 expected='Input must be rejected, no success message shown, balances and transaction history unchanged.'
 if 'Date filter' in r['name']:expected='Transactions on both selected boundary dates must appear, including when start and end are the same date.'
 heading('Expected');story.append(p(expected))
 heading('Observed')
 try:
  o=json.loads(r['observed'])
  if 'before' in o:
   def balances(v):return ', '.join(a['name']+': $'+a['balance'] for a in v['accounts'])
   summary=f"Submitted amount: {o.get('input',o.get('amount'))!r}. Before balances: {balances(o['before'])}. After balances: {balances(o['after'])}. History count changed from {len(o['before']['transactions'])} to {len(o['after']['transactions'])}."
   fresh=[t for t in o['after']['transactions'] if t['id'] not in {v['id'] for v in o['before']['transactions']}]
   if fresh:summary+=' New record: '+str({k:fresh[0].get(k) for k in ('id','amount','status','memo')})
  else:summary=json.dumps(o)
 except Exception:summary=r['observed'][:1800]
 story.append(p(summary));heading('Reproduce')
 for i,step in enumerate(r['steps'],1):story.append(p(str(i)+'. '+step,'SmallQA'))
 story.append(p('Evidence: artifacts-final/'+r['id']+'.png and '+r['id']+'.txt; raw observations in results.json.','SmallQA'))
 img=base/'artifacts-final'/r['evidence'][0]
 iw,ih=ImageReader(str(img)).getSize();scale=min(500/iw,315/ih)
 story.append(Image(str(img),width=iw*scale,height=ih*scale,hAlign='LEFT'))
 story.append(p('Suggested investigation: validate the business rule at the API boundary and repeat the same scenario against a freshly seeded target. This audit does not patch the target.','SmallQA'))
story.append(PageBreak());story.append(p('Scenario ledger','Heading1'))
table([['Test','Scenario','Verdict']]+[[r['id'],r['name'],r['verdict']] for r in data['scenarios']],[40,385,75])
story.append(PageBreak());story.append(p('Requirement-level coverage','Heading1'))
story.append(p('Each row preserves one official PRD bullet. Unverified includes partially exercised compound statements. Full mappings, retrieval scores and candidate tests are in results.json.','SmallQA'))
table([['ID','Requirement','Verdict / direct tests']]+[[r['id'],r['text'],r['status']+'\n'+', '.join(r['verified_by'])] for r in data['requirements']],[30,375,95])
story.append(PageBreak());story.append(p('Costs, limitations and handoff','Heading1'))
heading('Run cost');story.append(p('Model/API inference: $0.00. Remote model calls: 0. Billed input/output tokens: 0. Requirement planning runs locally with scikit-learn; there is no model price assumption. CPU, memory, browser video encoding, storage, development assistance, hosting and the entrant\'s time are excluded. No claim is made that total lifecycle cost is zero.'))
heading('What was not established');story.append(p('No claims about load capacity, concurrent transfer isolation, rollback under process crash, hidden data exposure, every mobile screen, exhaustive accessibility or all failure-retry states. PGlite serializes connections; no concurrency result can be inferred. Some compound PRD bullets remain unverified. The prototype uses known DemoBank scenario adapters and does not autonomously invent arbitrary actions.'))
heading('Development and verification');story.append(p('Prepared with ChatGPT/Codex assistance. The entrant should review the source, understand each finding, and confirm organizer policy on assisted development. Three planner unit tests passed and the supplied frontend TypeScript check passed. Defect claims are based on executed browser observations, with read-only API observations for side effects.'))
heading('Before submission');story.append(p('Fork the official kit, publish the agent in the fork, upload the video/report/evidence with judge-readable permissions, and confirm every link while signed out. Submit through the organizer Google Form by October 21, 2026 at 6 PM Eastern / 5 PM Central. The local package is not itself a public repository or form submission.'))
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#67788c'));c.drawString(48,26,'SpecLens | CDF QA Hackathon | Local demonstration');c.drawRightString(548,26,str(d.page))
SimpleDocTemplate(str(out/'SpecLens_QA_Audit.pdf'),title='SpecLens QA Audit',author='Raashid Shaik',pagesize=(596,842),rightMargin=48,leftMargin=48,topMargin=44,bottomMargin=44).build(story,onFirstPage=footer,onLaterPages=footer)
(out/'Cost_Breakdown.json').write_text(json.dumps(data['cost']|{'runtime_seconds':data['runtime_seconds'],'environment':data['environment']},indent=2))
