import json,pathlib,subprocess,sys
import stnlab,stnlab.oracle,stnlab.__main__
for m in [stnlab,stnlab.oracle,stnlab.__main__]:assert 'site-packages' in m.__file__,m.__file__
controls=json.load(open(sys.argv[1]));commands=[[sys.executable,'-m','stnlab'],[sys.argv[2]]]
for k,c in enumerate(controls):
 inp=pathlib.Path(f'input-{k}.json');inp.write_text(json.dumps(c['input']))
 expected=stnlab.analyze(c['input']);assert stnlab.verify(expected)
 for j,command in enumerate(commands):
  out=f'report-{k}-{j}.json';subprocess.run(command+[str(inp),'--output',out],check=True);assert json.load(open(out))==expected
  p=subprocess.run(command+[out,'--verify'],check=True,capture_output=True,text=True);assert json.loads(p.stdout)=={'valid':True,'schema':'stnlab-v1'}
print(f'Installed: {len(controls)} controls, both CLI entry points generation/verification, three site-packages origins, outside checkout')

import stnlab.insertions
assert 'site-packages' in stnlab.insertions.__file__
controls=json.load(open(sys.argv[3]));commands=[[sys.executable,'-m','stnlab.insertions'],[sys.argv[4]]]
for k,c in enumerate(controls):
 inp=pathlib.Path(f'insertion-input-{k}.json');inp.write_text(json.dumps(c['input']))
 expected=stnlab.insertions.analyze(c['input']);assert stnlab.insertions.verify(expected)
 for j,command in enumerate(commands):
  out=f'insertion-report-{k}-{j}.json';subprocess.run(command+[str(inp),'--output',out],check=True);assert json.load(open(out))==expected
  q=subprocess.run(command+[out,'--verify'],check=True,capture_output=True,text=True);assert json.loads(q.stdout)=={'valid':True,'schema':'stnlab-insertions-v1'}
print(f'Installed insertion family: {len(controls)} controls, both CLI entry points generation/verification, four total site-packages origins, outside checkout')
