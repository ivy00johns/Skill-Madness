from pathlib import Path
import subprocess, os, json, re
E=Path(__file__).resolve().parent
os.environ.update(TMPDIR=str(E/'test-temp'),BATS_TMPDIR=str(E/'test-temp'),PYTHONDONTWRITEBYTECODE='1',PATH=str(E/'test-bin')+os.pathsep+os.environ['PATH'])
with open(E/'tests-run-all-corrected.txt','w') as f:
 f.write('$ bash tests/run-all.sh --tap (snapshot includes tracked .scan-skills-ignore)\n'); f.flush()
 p=subprocess.run(['bash','tests/run-all.sh','--tap'],cwd=E/'test-snapshot',stdout=f,stderr=subprocess.STDOUT)
 f.write('\nEXIT_CODE='+str(p.returncode)+'\n')
t=(E/'tests-run-all-corrected.txt').read_text(); ok=re.findall(r'^ok .*$',t,re.M)
(E/'corrected-test-summary.json').write_text(json.dumps({'exit_code':p.returncode,'plan':re.findall(r'^1\.\.\d+',t,re.M),'passed':sum('# skip' not in x for x in ok),'skipped':[x for x in ok if '# skip' in x],'failed':re.findall(r'^not ok .*$',t,re.M)},indent=2)+'\n')
