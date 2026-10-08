"""Audit-only tests: every filesystem write is under this script's parent."""
from pathlib import Path
import os, json, subprocess, hashlib, re, collections
R = Path(__file__).resolve().parents[4]
E = Path(__file__).resolve().parent
S = E/'test-snapshot'
F = E/'adversarial-fixtures'; F.mkdir(exist_ok=True)
env=dict(os.environ, TMPDIR=str(E/'test-temp'), PYTHONDONTWRITEBYTECODE='1', PATH=str(E/'test-bin')+os.pathsep+os.environ['PATH'])
log=[]
def run(label, args, cwd=R, extra=None):
    p=subprocess.run(args,cwd=cwd,env=dict(env,**(extra or {})),input='',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log.extend(['\n## '+label,'$ '+' '.join(map(str,args)),p.stdout,'EXIT_CODE='+str(p.returncode)])
    return p
inline=F/'inline'; inline.mkdir(exist_ok=True)
(inline/'index.html').write_text('<main style="display:grid;grid-template-columns:60% 40%;width:1200px">Hello</main>\n')
hashed=F/'hashed'; hashed.mkdir(exist_ok=True)
chrome='<header><nav><a href="/">Home</a></nav></header><footer>Copyright Example</footer>'
for i in range(4):
    (hashed/f'page-{i}.html').write_text(f'{chrome}<main class="c-a9{i}f">Page {i}</main>\n')
(hashed/'style.css').write_text('\n'.join(f'.c-a9{i}f {{ display: grid; gap: 1rem; grid-template-columns: 1fr; }}' for i in range(4)))
for label,d in [('inline',inline),('unique CSS classes and shared chrome copies',hashed)]:
    for checker in ['design-token-guard/scripts/check_design_tokens.py','class-extraction-guard/scripts/check_class_extraction.py']:
        run(label+' / '+checker,['python3',str(R/'skills/workflows'/checker),'--root',str(d),'--json'])
# Missing validator on strict QA profile, with a present report (not missing-report policy).
q=F/'strict-hook'; q.mkdir(exist_ok=True)
(q/'qa-gate.sh').write_bytes((R/'hooks/scripts/qa-gate.sh').read_bytes())
(q/'qa-report.json').write_text('{}\n')
run('strict QA hook without validator',['bash',str(q/'qa-gate.sh')],q,{'ATS_HOOK_PROFILE':'strict'})
# Freshly generated scripts/references/assets routing in pure plan.
p=run('plan for fresh Copilot, Gemini and Claude output',['bash','scripts/install-plan.sh','--tool','copilot,gemini-cli,claude-code','--integrations',str(E/'generated-sequential'),'--root',str(F/'install-root')])
plan=json.loads(p.stdout); (E/'fresh-install-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
ops=plan['operations']; summary={'operations':len(ops),'copilot_script_operations':sum(o['tool']=='copilot' and '-scripts/' in o['source'] for o in ops),'copilot_reference_operations':sum(o['tool']=='copilot' and '-references/' in o['source'] for o in ops),'gemini_manifest_operations':sum('gemini-extension.json' in o['source'] for o in ops),'claude_hooks_operations':sum('/hooks/' in o['source'] or o['source'].endswith('/hooks.json') for o in ops),'source_assets':len(list((R/'skills').rglob('assets/*'))),'generated_asset_files':len([x for x in (E/'generated-sequential').rglob('*') if x.is_file() and 'assets' in x.parts])}
(E/'resource-delivery-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# Source changed after planning; executable copy and installed state hash.
home=F/'apply-root'; home.mkdir(exist_ok=True)
src=F/'executable.sh'; src.write_text('#!/bin/sh\nprintf old\n'); src.chmod(0o755)
oldhash=hashlib.sha256(src.read_bytes()).hexdigest()
dest=home/'scripts/executable.sh'; escape=F/'outside-declared-root/copied.sh'
custom={'schema_version':1,'profile':'full','tools':['claude-code'],'operations':[{'source':str(src),'dest':str(d),'sha256':oldhash,'action':'create','tool':'claude-code'} for d in [dest,escape]]}
cp=F/'apply-plan.json'; cp.write_text(json.dumps(custom))
src.write_text('#!/bin/sh\nprintf changed-after-plan\n')
run('apply stale source plan with destination outside declared root',['bash','scripts/install-apply.sh','--plan',str(cp),'--root',str(home)])
state=json.loads((home/'.claude/.ats-install-state.json').read_text())
log.append(json.dumps({'source_mode':oct(src.stat().st_mode&0o777),'dest_mode':oct(dest.stat().st_mode&0o777),'stored_hash_matches_installed_bytes':state['files'][0]['sha256']==hashlib.sha256(Path(state['files'][0]['dest']).read_bytes()).hexdigest(),'outside_root_destination_created':escape.exists()},indent=2))
# Worker entry uses snapshot root, never canonical root. Verify --out propagation directly.
run('parallel worker entry ignores custom --out',['bash','scripts/convert.sh','--tool','gemini-cli','--out',str(F/'worker-requested')],S,{'ATS_CONVERT_WORKER':'1','ATS_CONVERT_TOOL':'gemini-cli','OUT_DIR':str(F/'worker-requested')})
log.append(json.dumps({'worker_requested_output_exists':(F/'worker-requested').exists(),'worker_default_output_exists':(S/'integrations/gemini-cli').exists(),'worker_default_manifest_exists':(S/'integrations/gemini-cli/gemini-extension.json').exists()},indent=2))
run('gh PR view option verification',['gh','pr','view','--help'])
(E/'adversarial-results.txt').write_text('\n'.join(log)+'\n')
# Compact full-body audit evidence with stable numbered excerpts: all canonical active bodies.
inv=json.loads((E/'inventory.json').read_text()); excerpts=[]; compact=[]
for row in inv:
    p=R/row['path']; lines=p.read_text().splitlines(); fm=row['frontmatter']
    compact.append(f"{fm['name']} | {row['path']} | {row['body_words']} words/{row['lines']} lines | cc={fm.get('requires_claude_code',False)} | tools={fm.get('allowed-tools',[])}")
    excerpts.append('\n=== '+row['path']+' ===\n'+'\n'.join(f'{n}: {v}' for n,v in enumerate(lines,1)))
(E/'all-active-skills-numbered.txt').write_text('\n'.join(excerpts)+'\n')
(E/'inventory-compact.txt').write_text('\n'.join(compact)+'\n')
# References: literal resource mentions only. Placeholder/code examples need manual triage.
missing=[]
for row in inv:
    p=R/row['path']; text=p.read_text()
    for match in re.finditer(r'(?:references|scripts|assets|template)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+',text):
        v=match.group(0)
        if not (p.parent/v).exists(): missing.append({'skill':row['frontmatter']['name'],'line':text[:match.start()].count('\n')+1,'reference':v})
(E/'literal-resource-misses.json').write_text(json.dumps(missing,indent=2)+'\n')
tap=(E/'tests-run-all.txt').read_text(); ok=re.findall(r'^ok \d+.*$',tap,re.M); bad=re.findall(r'^not ok .*$',tap,re.M)
(E/'test-summary.json').write_text(json.dumps({'tap_plan':re.findall(r'^1\.\.\d+',tap,re.M),'ok_lines':len(ok),'not_ok_lines':bad,'skipped':[v for v in ok if '# skip' in v],'process_exit_code':'UNVERIFIED: detached process; no wait status retained'},indent=2)+'\n')
print(json.dumps(summary,indent=2)); print('\n'.join(compact)); print('RESOURCE MISSES',json.dumps(missing,indent=2)); print('TAP',len(ok),len(bad)); print('\n'.join(log)[-5000:])
