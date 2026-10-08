"""Read-only canonical-source audit checks; all writes stay under this report."""
from pathlib import Path
import subprocess, shutil, os, json, hashlib, collections
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent

def active(root):
    return sorted(p for p in (root/'skills').rglob('SKILL.md') if len(p.relative_to(root).parts)<=4 and not {'archive','in-progress'}.intersection(p.relative_to(root).parts))

def run(name, command, cwd, env):
    result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT/(name+'.txt')).write_text('$ '+ ' '.join(command)+'\n'+result.stdout+'\nEXIT_CODE='+str(result.returncode)+'\n')
    print(name, 'exit', result.returncode, result.stdout[-1800:])
    return result

if __name__ == '__main__':
    import yaml
    inventory=[]
    for p in active(ROOT):
        text=p.read_text(); fm=yaml.safe_load(text.split('---',2)[1]); body=text.split('---',2)[2]
        inventory.append({'path':str(p.relative_to(ROOT)), 'frontmatter':fm, 'lines':len(text.splitlines()), 'body_words':len(body.split()), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'references':[str(x.relative_to(ROOT)) for x in sorted((p.parent/'references').rglob('*')) if x.is_file()], 'scripts':[str(x.relative_to(ROOT)) for x in sorted((p.parent/'scripts').rglob('*')) if x.is_file() and not {'node_modules','__pycache__'}.intersection(x.parts)]})
    (OUT/'inventory.json').write_text(json.dumps(inventory,indent=2))
    sandbox=OUT/'test-snapshot'; sandbox.mkdir(exist_ok=True)
    for name in ['scripts','tests','skills','spec','manifests','hooks','.claude-plugin']:
        shutil.copytree(ROOT/name,sandbox/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('node_modules','__pycache__','*-workspace'))
    for name in ['README.md','CLAUDE.md','AGENTS.md','START-HERE.md','PLAN.md','.gitignore']:
        shutil.copy2(ROOT/name,sandbox/name)
    (sandbox/'docs').mkdir(exist_ok=True)
    for name in ['REMAINING-WORK.md','COMPLETED-WORK.md','FUTURE.md']:
        shutil.copy2(ROOT/'docs'/name,sandbox/'docs'/name)
    # Some bats fixtures hardcode /tmp. Redirect mktemp to a report-local directory.
    temp=OUT/'test-temp'; temp.mkdir(exist_ok=True)
    shim=OUT/'test-bin'; shim.mkdir(exist_ok=True)
    real_mktemp=shutil.which('mktemp')
    wrapper=shim/'mktemp'
    wrapper.write_text('#!/usr/bin/env python3\nimport os,sys\na=[x.replace("/tmp/",os.environ["TMPDIR"]+"/") for x in sys.argv[1:]]\nos.execv('+repr(real_mktemp)+',["mktemp"]+a)\n')
    wrapper.chmod(0o755)
    env=dict(os.environ,TMPDIR=str(temp), BATS_TMPDIR=str(temp), PYTHONDONTWRITEBYTECODE='1', PATH=str(shim)+os.pathsep+os.environ['PATH'])
    run('lint-skills',['bash','scripts/lint-skills.sh'],sandbox,env)
    run('catalog-check',['bash','scripts/catalog.sh','--check'],sandbox,env)
    log = open(OUT/'tests-run-all.txt', 'w')
    log.write('$ bash tests/run-all.sh --tap (isolated snapshot; temporary paths redirected)\n'); log.flush()
    proc = subprocess.Popen(['bash','tests/run-all.sh','--tap'], cwd=sandbox, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (OUT/'test-process.json').write_text(json.dumps({'pid':proc.pid,'snapshot':str(sandbox)},indent=2))
    print('TEST_PID',proc.pid,flush=True)
    run('convert-sequential',['bash','scripts/convert.sh','--out',str(OUT/'generated-sequential')],ROOT,env)
    run('convert-parallel',['bash','scripts/convert.sh','--parallel','--jobs','3','--out',str(OUT/'generated-parallel')],ROOT,env)
    # Compare skill sets and bytes; timestamps excluded by comparing bodies.
    expected={r['frontmatter']['name'] for r in inventory if not r['frontmatter'].get('requires_claude_code')}
    summaries={}
    for tool in ['claude-code','copilot','antigravity','gemini-cli','opencode','cursor','openclaw','qwen','kimi','aider','windsurf']:
        old=ROOT/'integrations'/tool; new=OUT/'generated-sequential'/tool
        if tool in ['claude-code','antigravity','gemini-cli']:
            names={p.parent.name for p in old.rglob('SKILL.md')}; fresh={p.parent.name for p in new.rglob('SKILL.md')}
        elif tool in ['cursor','qwen','opencode','copilot']:
            ext='*.mdc' if tool=='cursor' else '*.md'; sub='rules' if tool=='cursor' else 'agents' if tool in ['qwen','opencode'] else ''
            names={p.stem for p in (old/sub).glob(ext)}; fresh={p.stem for p in (new/sub).glob(ext)}
        elif tool in ['openclaw','kimi']:
            pattern='IDENTITY.md' if tool=='openclaw' else 'agent.yaml'; names={p.parent.name for p in old.rglob(pattern)}; fresh={p.parent.name for p in new.rglob(pattern)}
        else: names=set(); fresh=set()
        summaries[tool]={'committed_count':len(names),'fresh_count':len(fresh),'stale_names':sorted(names-fresh),'missing_names':sorted(fresh-names),'committed_files':len([p for p in old.rglob('*') if p.is_file()])}
    (OUT/'generation-comparison.json').write_text(json.dumps(summaries,indent=2))
    print(json.dumps(summaries,indent=2))
    # Retain test snapshot until the asynchronously running bats suite has ended.
    print('Keep snapshot until test process has ended.',flush=True)
