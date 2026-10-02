from pathlib import Path
import subprocess, os, json, shutil, importlib.util, sys, re
R=Path(__file__).resolve().parents[4]; E=Path(__file__).resolve().parent; F=E/'adversarial-fixtures'; S=E/'test-snapshot'
env=dict(os.environ,TMPDIR=str(E/'test-temp'),BATS_TMPDIR=str(E/'test-temp'),PYTHONDONTWRITEBYTECODE='1',PATH=str(E/'test-bin')+os.pathsep+os.environ['PATH'])
logs=[]
def run(label,cmd,cwd=R,extra=None):
 p=subprocess.run(cmd,cwd=cwd,env=dict(env,**(extra or {})),text=True,input='',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 logs.extend(['\n## '+label,'$ '+' '.join(map(str,cmd)),p.stdout,'EXIT_CODE='+str(p.returncode)])
 return p
# Correct audit snapshot only: ignore file is part of canonical tracked input.
shutil.copy2(R/'.scan-skills-ignore',S/'.scan-skills-ignore')
run('scan suite after restoring omitted tracked ignore input',['bats','--tap','tests/scan-skills/01-scan-skills.bats'],S)
run('canonical skill scan',['bash','scripts/scan-skills.sh','--check','skills/'])
# Literal HTML dimensions are missed by quoted-string regex; JSX is detected but warning-pass.
(F/'inline/component.tsx').write_text('export const X = () => <main style={{display: "grid", width: "1200px"}}>Hi</main>;\n')
checker=R/'skills/workflows/design-token-guard/scripts/check_design_tokens.py'
run('HTML plus JSX inline styles / default',['python3',str(checker),'--root',str(F/'inline'),'--json'])
strict=F/'strict-design.json'; strict.write_text(json.dumps({'inlineStyleMode':'strict','rules':{'no-inline-style':'error'}}))
run('HTML plus JSX / strict policy refutation',['python3',str(checker),'--root',str(F/'inline'),'--config',str(strict),'--json'])
badbin=F/'git-failure-bin'; badbin.mkdir(exist_ok=True)
(badbin/'git').write_text('#!/bin/sh\nexit 2\n'); (badbin/'git').chmod(0o755)
run('staged design check with git unavailable',['python3',str(checker),'--root',str(F/'inline'),'--staged','--json'],extra={'PATH':str(badbin)+os.pathsep+env['PATH']})
# Direct worker-entry test exposes installer dry-run reset safely in report-local fake HOME.
home=F/'worker-home'; home.mkdir(exist_ok=True)
shutil.copy2(E/'generated-sequential/gemini-cli/gemini-extension.json',S/'integrations/gemini-cli/gemini-extension.json')
run('installer worker loses exported dry-run',['bash','scripts/install.sh','--tool','gemini-cli','--dry-run','--no-interactive'],S,{'HOME':str(home),'ATS_INSTALL_WORKER':'1','ATS_INSTALL_TOOL':'gemini-cli','DRY_RUN':'true'})
logs.append('worker wrote despite dry-run: '+str((home/'.gemini/extensions/alltheskills').exists()))
# Mock only the subprocess boundary: no Hermes binary, network, credentials or global installs.
sys.path.insert(0,str(R/'skills/workflows/skill-creator'))
p=R/'skills/workflows/skill-creator/scripts/run_eval.py'; spec=importlib.util.spec_from_file_location('audit_run_eval',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
calls=[]
def fake(query,name,path,timeout):
 calls.append([query,name,path,timeout]); return False
m.run_single_query=fake
for desc in ['original description','radically different candidate']:
 result=m.run_eval([{'query':'audit negative control','should_trigger':False}],'skill',''+desc,'same-source',1,10)
 logs.append('description='+repr(desc)+' calls='+json.dumps(calls[-1])+' result='+json.dumps(result))
logs.append('Static call chain: run_eval accepts description but never forwards/applies it; negative-control failures become False and count as correct non-trigger.')
# Numbered multi-file excerpts for all high-impact claims and supporting references.
paths=['scripts/convert.sh','scripts/install.sh','scripts/install-plan.sh','scripts/install-apply.sh','spec/PSFS.md','spec/frontmatter.schema.json','scripts/lint-skills.sh','scripts/catalog.sh','.github/workflows/lint-skills.yml','hooks/hooks.manifest.json','hooks/scripts/qa-gate.sh','hooks/scripts/qa-gate-validate.py','.scan-skills-ignore','skills/workflows/sync-skills/scripts/sync-skills.sh','skills/orchestrator/references/phase-guide.md','skills/orchestrator/references/file-ownership.md','skills/orchestrator/references/agent-spawning.md','skills/loops/loop-controller/references/safety.md','skills/loops/loop-controller/references/primitives.md','skills/workflows/design-token-guard/scripts/check_design_tokens.py','skills/workflows/class-extraction-guard/scripts/check_class_extraction.py','skills/workflows/prose-slop-guard/scripts/check_prose_slop.py','skills/workflows/skill-creator/scripts/run_eval.py','skills/workflows/skill-creator/scripts/run_loop.py','skills/meta/model-adaptation/references/long-run-hygiene.md','skills/meta/model-adaptation/references/model-effort-tiering.md','README.md','CLAUDE.md','START-HERE.md','docs/COMPLETED-WORK.md','docs/FUTURE.md']
(E/'supporting-source-numbered.txt').write_text('\n'.join('\n=== '+v+' ===\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate((R/v).read_text().splitlines(),1)) for v in paths)+'\n')
(E/'refutation-checks.txt').write_text('\n'.join(logs)+'\n'); print('\n'.join(logs)[-11000:])
# Baseline and boundary evidence, without secret values or user-installed skill bodies.
commands=[['git','rev-parse','HEAD'],['git','status','--short'],['git','ls-files','integrations'],['git','check-ignore','integrations/claude-code'],['git','worktree','list','--porcelain']]
b=[]
for cmd in commands:
 p=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); b.extend(['$ '+' '.join(cmd),p.stdout,'EXIT_CODE='+str(p.returncode)])
inv=json.loads((E/'inventory.json').read_text()); cats={}
for x in inv:
 cat=x['path'].split('/')[1]; cats.setdefault(cat,{'active':0,'gated':0}); cats[cat]['active']+=1; cats[cat]['gated']+=bool(x['frontmatter'].get('requires_claude_code',False))
b.append(json.dumps({'categories':cats,'active':len(inv),'gated':sum(x['frontmatter'].get('requires_claude_code',False) for x in inv),'root_env_present':(R/'.env').exists(),'skill_workspace_dirs':[str(p.relative_to(R)) for p in (R/'skills').rglob('*-workspace*') if p.is_dir()]},indent=2))
(E/'baseline.txt').write_text('\n'.join(b)+'\n')
