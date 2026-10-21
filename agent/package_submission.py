from pathlib import Path
import json, zipfile, subprocess, shutil, hashlib
base=Path(__file__).resolve().parent;root=base.parent;out=root.parent/'output/qa-submission';out.mkdir(parents=True,exist_ok=True)
d=json.loads((base/'artifacts-final/results.json').read_text())
assert len(d['scenarios'])==22, 'Run is incomplete'
assert d['runtime_seconds']>=180,'Recorded run has not closed yet'
subprocess.run(['python','export_report.py'],cwd=base,check=True)
video=max((base/'artifacts-final/video').glob('*.webm'),key=lambda p:p.stat().st_mtime)
subprocess.run(['ffmpeg','-y','-i',str(video),'-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'SpecLens_Walkthrough.mp4')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-of','json',str(out/'SpecLens_Walkthrough.mp4')]))
assert 180<=float(probe['format']['duration'])<=300,probe
with zipfile.ZipFile(out/'SpecLens_Source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in root.rglob('*'):
  rel=f.relative_to(root);parts=rel.parts
  if not f.is_file() or any(x in parts for x in ('.git','node_modules','__pycache__','.pytest_cache','.venv','dist')):continue
  if any(x.startswith('artifacts-') for x in parts) or f.name.endswith('-service.log') or f.suffix=='.tsbuildinfo':continue
  z.write(f,'SpecLens/'+str(rel))
with zipfile.ZipFile(out/'SpecLens_Evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (base/'artifacts-final').glob('*'):
  if f.is_file():z.write(f,'artifacts-final/'+f.name)
 z.write(root/'test-website/PRD.md','PRD.md')
summary={'scenario_counts':d['scenario_counts'],'requirement_counts':{s:sum(r['status']==s for r in d['requirements']) for s in ('passed','failed','unverified')},'duration_seconds':float(probe['format']['duration']),'source_commit':'c7b856cc0d7cfb367e96fda0e5c291eba10cbb10','prd_sha256':d['prd_sha256']}
(out/'Verification_Summary.json').write_text(json.dumps(summary,indent=2))
with zipfile.ZipFile(out/'SpecLens_Complete_Submission.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in out.iterdir():
  if f.is_file() and f.name!='SpecLens_Complete_Submission.zip':z.write(f,f.name)
print(json.dumps(summary,indent=2))
print([(f.name,f.stat().st_size) for f in out.iterdir() if f.is_file()])
