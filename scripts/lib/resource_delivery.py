"""Shared delivery contract (stdlib): inventory bytes/modes, not host acceptance.

No credentials, dependency installations or native hook activation are implied.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

TOOLS = ('claude-code', 'copilot', 'antigravity', 'gemini-cli', 'opencode',
         'cursor', 'openclaw', 'qwen', 'kimi', 'aider', 'windsurf')
RESOURCE_DIRS = ('references', 'scripts', 'assets', 'agents', 'eval-viewer',
                 'template', 'templates', 'sources')
EXCLUDED = {'.git', '__pycache__', 'node_modules', '.workspaces', 'dist', 'build'}
MANIFEST = '.ats-resources.json'
RUNTIME = '.ats-runtime.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.ats-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(value, out, indent=2, sort_keys=True)
            out.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('invalid relative resource path')
    path = Path(value)
    if path.is_absolute() or any(p in ('.', '..') for p in path.parts):
        raise ValueError('unsafe resource path: ' + value)
    return path


def contained(path, root):
    path, root = Path(os.path.abspath(path)), Path(os.path.abspath(root))
    if path == root or root not in path.parents:
        raise ValueError('destination outside approved root: ' + str(path))
    # Refuse symlink parents and the leaf, even if they currently resolve inside.
    for parent in (path, *path.parents):
        if parent == root:
            if parent.is_symlink():
                raise ValueError('symlinked approved root')
            break
        if parent.is_symlink():
            raise ValueError('symlinked destination boundary: ' + str(parent))
    return path


def file_record(filename, **fields):
    path = Path(filename)
    if path.is_symlink() or not path.is_file():
        raise ValueError('resource is not a regular file: ' + str(path))
    return dict(fields, sha256=digest(path.read_bytes()), mode=stat.S_IMODE(path.stat().st_mode))


def discover(skills_root):
    root = Path(skills_root)
    files = sorted(set(root.glob('*/SKILL.md')) | set(root.glob('*/*/SKILL.md')))
    result = []
    for file in files:
        parts = file.relative_to(root).parts
        if parts[0] in ('archive', 'in-progress'):
            continue
        slug = file.parent.name
        category = parts[0]
        result.append((file, category, slug))
    return result


def selected(category, slug, targets):
    return not targets or category in targets or slug in targets or category + '/' + slug in targets


def layout(tool, category, slug):
    """Resource root and prompt paths relative to integrations/<tool>."""
    if tool == 'claude-code':
        root = category + '/' + slug
        return root, [root + '/SKILL.md']
    if tool == 'gemini-cli':
        root = 'skills/' + slug
        return root, [root + '/SKILL.md']
    if tool in ('antigravity', 'openclaw', 'kimi'):
        names = {'antigravity': ['SKILL.md'], 'openclaw': ['SOUL.md', 'AGENTS.md', 'IDENTITY.md'],
                 'kimi': ['agent.yaml', 'system.md']}[tool]
        return slug, [slug + '/' + n for n in names]
    prefix = {'opencode': 'agents/', 'qwen': 'agents/', 'cursor': 'rules/'}.get(tool, '')
    if tool in ('aider', 'windsurf'):
        return 'skills/' + slug, ['CONVENTIONS.md' if tool == 'aider' else '.windsurfrules']
    return prefix + slug + '-resources', [prefix + slug + ('.mdc' if tool == 'cursor' else '.md')]


def resource_files(root):
    root = Path(root)
    result = []
    for name in RESOURCE_DIRS:
        folder = root / name
        if folder.is_symlink():
            raise ValueError('symlinked resource folder: ' + str(folder))
        if not folder.exists():
            continue
        for parent, dirs, files in os.walk(folder, onerror=lambda e: (_ for _ in ()).throw(e)):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.endswith('-workspace'))
            for d in dirs:
                if (Path(parent) / d).is_symlink():
                    raise ValueError('symlinked resource directory: ' + d)
            for name in sorted(files):
                if name == '.DS_Store' or name.startswith('.env') or name.endswith(('.pyc', '.pem', '.key')):
                    continue
                file = Path(parent) / name
                file_record(file)  # validate before any copy
                result.append(file)
    return result


def source_diagnostics(skill):
    """Check bundled regular files and literal local resource references, not host execution."""
    skill = Path(skill)
    files = resource_files(skill.parent)
    owned = {p.relative_to(skill.parent).as_posix() for p in files}
    text = skill.read_text(encoding='utf-8')
    roots = '|'.join(RESOURCE_DIRS)
    matches = list(re.finditer(r'`((?:' + roots + r')/[a-zA-Z0-9_.\-/]+)`', text))
    references = {m.group(1) for m in matches}
    missing, dependencies, outputs = set(), set(), set()
    checkout = next((p for p in skill.parents if (p / '.env.example').is_file()), None)
    library = discover(checkout / 'skills') if checkout else []
    for match in matches:
        value = match.group(1)
        if value in owned or value.endswith('/') or (skill.parent / value).is_dir():
            continue
        # Context-qualified references belong to another skill, not this bundle.
        # Report those dependencies explicitly rather than pretending they ship.
        start = text.rfind('\n\n', 0, match.start())
        end = text.find('\n\n', match.end())
        context = text[max(0, start):end if end >= 0 else len(text)]
        owners = [(source.parent, slug) for source, _, slug in library
                  if source.parent != skill.parent and slug in context
                  and (source.parent / value).is_file()]
        if owners:
            dependencies.update(slug + '/' + value for _, slug in owners)
        elif checkout and (checkout / value).is_file():
            dependencies.add('checkout/' + value)
        elif re.search(r'\b(create|write|generate)\b', context, re.I) and value.startswith(('template/', 'templates/')):
            outputs.add(value)
        else:
            missing.add(value)
    return {'files': len(files), 'bytes': sum(p.stat().st_size for p in files),
            'literal_references': len(references), 'missing': sorted(missing),
            'external_dependencies': sorted(dependencies), 'project_outputs': sorted(outputs)}


def copy_tree(source, destination):
    source, destination = Path(source), Path(destination)
    # The same exclusion/regular-file validation as bundled roots; no symlinks.
    files = resource_files(source.parent)
    for src in files:
        if source not in src.parents:
            continue
        dst = contained(destination / src.relative_to(source), destination.parent)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def prepare(tool_root, tool):
    tool_root = Path(tool_root)
    receipt = tool_root / MANIFEST
    if not receipt.exists():
        return
    data = read_json(receipt)
    if data.get('schema_version') != 1 or data.get('tool') != tool:
        raise ValueError('invalid previous resource manifest')
    # Generated outputs only: remove recorded files, never glob unrelated files.
    paths = [contained(tool_root / relative(r['path']), tool_root) for r in data['files']]
    for path in paths:
        if path.exists():
            if not path.is_file():
                raise ValueError('previous output is not a file')
            path.unlink()
    receipt.unlink()


def bundle(skill, tool_root, tool, category, slug):
    skill, tool_root = Path(skill), Path(tool_root)
    root_rel, prompts = layout(tool, category, slug)
    root = tool_root / root_rel
    files = resource_files(skill.parent)
    diagnostics = source_diagnostics(skill)
    if diagnostics['missing']:
        raise ValueError('missing local resources: ' + ', '.join(diagnostics['missing']))
    if skill.parent.name == 'skill-creator':
        required = ['agents/grader.md', 'assets/eval_review.html', 'eval-viewer/generate_review.py', 'eval-viewer/viewer.html']
        if any(not (skill.parent / p).is_file() for p in required):
            raise ValueError('skill-creator required helper resources missing')
    contained(root / '.boundary-check', tool_root)
    root.mkdir(parents=True, exist_ok=True)
    for src in files:
        dst = contained(root / src.relative_to(skill.parent), tool_root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    # Flat/consolidated formats also retain a usable skill-root prompt. Native
    # Claude's original prompt is never rewritten; legacy flat companions stay.
    if tool != 'claude-code' and tool != 'gemini-cli' and tool != 'antigravity':
        if tool in ('copilot', 'opencode', 'qwen', 'cursor'):
            text = (tool_root / prompts[0]).read_text()
            if tool == 'cursor':
                text = text.replace('---\n', '---\nname: ' + slug + '\n', 1)
            (root / 'SKILL.md').write_text(text)
        else:
            (root / 'SKILL.md').write_text(skill.read_text())
    # Standard companion roots export standard types, never native arrays.
    # Antigravity's host-specific risk/source/date_added header is already scalar
    # and must retain its established delivery contract, like native Claude.
    if tool not in ('claude-code', 'antigravity'):
        from standard_export import export
        (root / 'SKILL.md').write_text(export(skill.read_text()), encoding='utf-8')
    # Repo-maintenance consumers must use the actual checkout, not pretend their
    # installed directory is a repository. No root helpers/credentials copied.
    checkout = []
    text = skill.read_text()
    for helper in ('scripts/catalog.sh', 'scripts/scan-skills.sh', 'scripts/convert.sh'):
        if helper in text:
            checkout.append(helper)
    if slug == 'sync-skills':
        checkout.extend(['scripts/convert.sh', 'scripts/lib/resource_delivery.py'])
    checkout.extend(p.removeprefix('checkout/') for p in diagnostics['external_dependencies'] if p.startswith('checkout/'))
    runtime = {'schema_version': 1, 'skill': slug, 'category': category,
               'skill_dependencies': [p for p in diagnostics['external_dependencies'] if not p.startswith('checkout/')],
               'skill_root': '.', 'runtime': 'project toolchain; Python 3.10+ for creator/nano helpers' if slug in ('skill-creator', 'nano-banana') else 'project toolchain; Python 3.9+ for delivery helpers',
               'checkout_dependencies': sorted(set(checkout)),
               'secrets': 'explicit process environment; optional ATS_ENV_FILE selected by owner; never bundled',
               'resources': [str(p.relative_to(skill.parent)) for p in files]}
    atomic_json(root / RUNTIME, runtime)
    if files and tool in ('copilot', 'opencode', 'cursor', 'qwen', 'kimi'):
        prompt = tool_root / prompts[-1]
        note = '\n> Resource contract: set SKILL_ROOT to `%s` relative to this prompt directory; read `.ats-runtime.json`. Resolve local scripts/templates from that root, not Claude home or project cwd. Missing checkout dependencies/tools are BLOCKED; credentials are explicit environment input.\n' % os.path.relpath(root, prompt.parent)
        with prompt.open('a') as out:
            out.write(note)


def finish(tool_root, tool, skills_root):
    tool_root = Path(tool_root)
    records, skills = [], []
    for source, category, slug in discover(skills_root):
        root_rel, prompts = layout(tool, category, slug)
        runtime = tool_root / root_rel / RUNTIME
        if not runtime.is_file():
            continue
        skills.append({'slug': slug, 'category': category, 'root': root_rel, 'prompts': prompts})
        owned = set()
        for path in (tool_root / root_rel).rglob('*'):
            if path.is_file() or path.is_symlink():
                owned.add(path)
        for prompt in prompts:
            if (tool_root / prompt).exists():
                owned.add(tool_root / prompt)
        # Preserve PF1/reference legacy locations while the stable resource root
        # supplies local imports/relative helper paths for flat formats.
        if tool in ('copilot', 'opencode', 'qwen', 'cursor'):
            base = (tool_root / prompts[0]).parent
            for suffix in ('-references', '-scripts'):
                folder = base / (slug + suffix)
                if folder.exists():
                    owned.update(p for p in folder.rglob('*') if p.is_file() or p.is_symlink())
        for path in sorted(owned):
            records.append(file_record(path, path=str(path.relative_to(tool_root)), slug=slug, category=category))
    if tool == 'gemini-cli' and (tool_root / 'gemini-extension.json').exists():
        records.append(file_record(tool_root / 'gemini-extension.json', path='gemini-extension.json', slug=None, category=None))
    if tool == 'claude-code':
        for path in sorted(tool_root.glob('hooks/**/*')) + [tool_root / 'hooks.json']:
            if path.is_file():
                records.append(file_record(path, path=str(path.relative_to(tool_root)), slug=None, category='hooks'))
    # Consolidated prompt paths belong to multiple skills; keep a single record.
    unique = {r['path']: r for r in records}
    for path, record in unique.items():
        if tool in ('aider', 'windsurf') and path in ('CONVENTIONS.md', '.windsurfrules'):
            record['slug'] = record['category'] = None
    atomic_json(tool_root / MANIFEST, {'schema_version': 1, 'tool': tool,
                'skills': skills, 'files': [unique[p] for p in sorted(unique)]})


def inventory(tool_root, tool):
    tool_root = Path(tool_root)
    data = read_json(tool_root / MANIFEST)
    if data.get('schema_version') != 1 or data.get('tool') != tool or not isinstance(data.get('files'), list):
        raise ValueError('invalid resource manifest')
    if not isinstance(data.get('skills'), list):
        raise ValueError('invalid resource owners')
    owners = {}
    for skill in data['skills']:
        if not isinstance(skill, dict) or not re.fullmatch('[a-z0-9][a-z0-9-]*', skill.get('slug', '')):
            raise ValueError('invalid resource skill')
        relative(skill['root'])
        owners[skill['slug']] = skill['category']
    seen = set()
    for record in data['files']:
        if record.get('slug') is not None and owners.get(record['slug']) != record.get('category'):
            raise ValueError('unrecognized resource owner')
        if record.get('category') == 'hooks' and tool != 'claude-code':
            raise ValueError('unexpected native hook resource')
        rel = relative(record['path'])
        if str(rel) in seen:
            raise ValueError('duplicate manifest resource')
        seen.add(str(rel))
        src = contained(tool_root / rel, tool_root)
        actual = file_record(src)
        if actual['sha256'] != record['sha256'] or actual['mode'] != record['mode']:
            raise ValueError('resource bytes/mode changed since conversion: ' + str(src))
    return data


def destinations(tool, rel, home, project):
    home, project = Path(home), Path(project)
    roots = {'claude-code': [home / '.claude/skills'],
             'copilot': [home / '.github/agents', home / '.copilot/agents'],
             'antigravity': [home / '.gemini/antigravity/skills'],
             'gemini-cli': [home / '.gemini/extensions/alltheskills'],
             'opencode': [project / '.opencode'], 'cursor': [project / '.cursor'],
             'qwen': [project / '.qwen'], 'openclaw': [home / '.openclaw/alltheskills'],
             'kimi': [home / '.config/kimi/agents'], 'aider': [project / '.ats-skills/aider'],
             'windsurf': [project / '.ats-skills/windsurf']}
    if tool == 'claude-code' and (rel.startswith('hooks/') or rel == 'hooks.json'):
        return [home / '.claude/ats-hooks' / (rel[6:] if rel.startswith('hooks/') else rel)]
    if tool == 'aider' and rel == 'CONVENTIONS.md':
        return [project / rel]
    if tool == 'windsurf' and rel == '.windsurfrules':
        return [project / rel]
    return [r / rel for r in roots[tool]]


def make_plan(integrations, tools, root, categories, profile, generated_at, include_hooks=False):
    root = Path(os.path.abspath(root))
    ops, missing = [], []
    for tool in tools:
        folder = Path(integrations).resolve() / tool
        if not folder.is_dir():
            print("[plan] WARN missing source for tool '%s': %s" % (tool, folder), file=__import__('sys').stderr)
            missing.append(tool)
            continue
        manifest = inventory(folder, tool)
        for record in manifest['files']:
            category = record.get('category')
            if category == 'hooks' and not include_hooks:
                continue
            if category and category != 'hooks' and category not in categories:
                continue
            if not categories:
                continue
            rel = record['path']
            for dest in destinations(tool, rel, root, root):
                contained(dest, root)
                existing = file_record(dest) if dest.exists() else None
                same = existing and all(existing[k] == record[k] for k in ('sha256', 'mode'))
                ops.append({'tool': tool, 'source': str(folder / rel), 'dest': str(dest),
                            'sha256': record['sha256'], 'mode': record['mode'],
                            'action': 'skip' if same else 'overwrite' if existing else 'create',
                            'dest_sha256': existing['sha256'] if existing else None,
                            'dest_mode': existing['mode'] if existing else None})
    if len(missing) == len(tools):
        raise ValueError('all requested tools have missing sources; no installable sources')
    return {'schema_version': 2, 'root': str(root), 'generated_at': generated_at,
            'profile': profile, 'tools': tools, 'operations': sorted(ops, key=lambda o: (o['tool'], o['dest']))}


def validate_plan(plan, root):
    root = Path(os.path.abspath(root))
    if not isinstance(plan, dict) or plan.get('schema_version') != 2 or plan.get('root') != str(root):
        raise ValueError('plan schema/root mismatch; regenerate and review the plan')
    if not isinstance(plan.get('tools'), list) or any(t not in TOOLS for t in plan['tools']):
        raise ValueError('invalid plan tools')
    if not isinstance(plan.get('operations'), list):
        raise ValueError('invalid plan operations')
    seen, validated = set(), []
    for op in plan['operations']:
        if not isinstance(op, dict) or op.get('tool') not in plan['tools'] or op.get('action') not in ('create', 'overwrite', 'skip'):
            raise ValueError('invalid plan operation')
        if not isinstance(op.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', op['sha256']):
            raise ValueError('invalid source hash')
        if type(op.get('mode')) is not int or not 0 <= op['mode'] <= 0o777:
            raise ValueError('invalid source mode')
        if not isinstance(op.get('source'), str) or not isinstance(op.get('dest'), str) or not Path(op['dest']).is_absolute():
            raise ValueError('invalid plan paths')
        src = Path(op['source'])
        if not src.is_absolute() or src.is_symlink():
            raise ValueError('invalid source path')
        dest = contained(op['dest'], root)
        if str(dest) in seen:
            raise ValueError('duplicate destination')
        seen.add(str(dest))
        source = file_record(src)
        data = src.read_bytes()
        if any(source[k] != op[k] for k in ('sha256', 'mode')) or digest(data) != op['sha256']:
            raise ValueError('source bytes/mode changed since review: ' + str(src))
        validated.append((op, data, dest))
    return validated


def replace_bytes(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.ats-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def apply_plan(plan, root, dry_run=False, record_state=True):
    root = Path(os.path.abspath(root))
    ops = validate_plan(plan, root)  # all sources/destinations before first write
    state_path = contained(root / '.claude/.ats-install-state.json', root)
    plan_path = contained(root / '.claude/.ats-install-plan.json', root)
    previous = read_json(state_path) if state_path.exists() else {'schema_version': 2, 'root': str(root), 'files': [], 'tools': []}
    if not isinstance(previous, dict) or previous.get('schema_version') != 2 or previous.get('root') != str(root) or not isinstance(previous.get('files'), list):
        raise ValueError('existing state schema/root mismatch; migrate explicitly')
    for item in previous['files']:
        contained(item['dest'], root)
        if type(item.get('mode')) is not int or not re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')):
            raise ValueError('invalid prior state binding')
    merged = {f['dest']: f for f in previous['files']}
    changed, backups = [], []
    created = updated = skipped = 0
    for op, data, dest in ops:
        actual = file_record(dest) if dest.exists() else None
        same = actual and all(actual[k] == op[k] for k in ('sha256', 'mode'))
        if same:
            skipped += 1
        else:
            # Reviewed destination precondition prevents clobbering intervening
            # user edits. Reapply is allowed only when already at reviewed bytes.
            if (actual['sha256'] if actual else None) != op.get('dest_sha256') or (actual['mode'] if actual else None) != op.get('dest_mode'):
                raise ValueError('destination changed since review: ' + str(dest))
            if actual:
                updated += 1
            else:
                created += 1
            changed.append((dest, data, op['mode']))
        merged[str(dest)] = {k: op[k] for k in ('dest', 'sha256', 'mode', 'tool', 'source')}
    if not dry_run:
        try:
            for dest, data, mode in changed:
                contained(dest, root)  # recheck just before replacement
                backups.append((dest, dest.read_bytes() if dest.exists() else None,
                                stat.S_IMODE(dest.stat().st_mode) if dest.exists() else None))
                replace_bytes(dest, data, mode)
            if record_state:
                import datetime
                state = dict(previous, schema_version=2, root=str(root), profile=plan.get('profile'),
                             applied_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                             tools=sorted(set(previous.get('tools', [])) | set(plan['tools'])),
                             files=sorted(merged.values(), key=lambda f: f['dest']))
                combined = dict(plan, operations=[dict(f, action='overwrite', dest_sha256=f['sha256'], dest_mode=f['mode']) for f in state['files']])
                combined['tools'] = state['tools']
                for path, value in ((plan_path, combined), (state_path, state)):
                    backups.append((path, path.read_bytes() if path.exists() else None,
                                    stat.S_IMODE(path.stat().st_mode) if path.exists() else None))
                    atomic_json(path, value)
        except Exception:
            for path, data, mode in reversed(backups):
                if data is None:
                    if path.exists():
                        path.unlink()
                else:
                    replace_bytes(path, data, mode)
            raise
    return 'created=%d updated=%d skipped=%d' % (created, updated, skipped)


def manage_state(command, root, dry_run=False, plan_file=None):
    root = Path(os.path.abspath(root))
    state_path = contained(root / '.claude/.ats-install-state.json', root)
    if not state_path.exists():
        print('no install-state (nothing to %s)' % command)
        return 0
    state = read_json(state_path)
    if state.get('schema_version') != 2 or state.get('root') != str(root) or not isinstance(state.get('files'), list):
        raise ValueError('state schema/root mismatch; reconcile old receipts explicitly')
    files = state['files']
    for item in files:
        contained(item['dest'], root)
        if not re.fullmatch('[0-9a-f]{64}', item['sha256']) or type(item['mode']) is not int:
            raise ValueError('invalid state file record')
    if command == 'list':
        print('profile:    %s' % state.get('profile'))
        print('tools:      %s' % ', '.join(state.get('tools', [])))
        for item in files:
            print('[%s] %s %s' % (item['tool'], item['sha256'][:12], item['dest']))
        return 0
    drift = []
    for item in files:
        path = Path(item['dest'])
        current = file_record(path) if path.exists() else None
        if not current or any(current[k] != item[k] for k in ('sha256', 'mode')):
            drift.append(item)
    if command == 'drift':
        for item in drift:
            print('%s: %s' % ('changed' if Path(item['dest']).exists() else 'removed', item['dest']))
        print('DRIFT: %d files' % len(drift) if drift else 'pristine: no drift')
        return 1 if drift else 0
    if command == 'repair':
        plan = read_json(plan_file or root / '.claude/.ats-install-plan.json')
        validate_plan(plan, root)  # stale/missing sources block the whole repair
        by_dest = {op['dest']: op for op in plan['operations']}
        ops = []
        for item in drift:
            op = dict(by_dest[item['dest']])
            path = Path(item['dest'])
            actual = file_record(path) if path.exists() else None
            op.update(action='overwrite' if actual else 'create',
                      dest_sha256=actual['sha256'] if actual else None,
                      dest_mode=actual['mode'] if actual else None)
            ops.append(op)
        plan = dict(plan, operations=ops)
        result = apply_plan(plan, root, dry_run)
        print(('would repair' if dry_run else 'repaired') + ': ' + result)
        return 0
    if drift:
        raise ValueError('uninstall refused: installed files changed; back up/reconcile before removing')
    if not dry_run:
        backups = []
        try:
            for item in files:
                path = Path(item['dest'])
                backups.append((path, path.read_bytes(), item['mode']))
                path.unlink()
            state_path.unlink()
            sibling = root / '.claude/.ats-install-plan.json'
            if sibling.exists():
                sibling.unlink()
        except Exception:
            for path, data, mode in backups:
                replace_bytes(path, data, mode)
            raise
    print('%s %d recorded files' % ('would remove' if dry_run else 'removed', len(files)))
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    copier = commands.add_parser('copy-tree')
    copier.add_argument('--source', required=True)
    copier.add_argument('--destination', required=True)
    preparer = commands.add_parser('prepare')
    preparer.add_argument('--tool-root', required=True)
    preparer.add_argument('--tool', required=True)
    bundler = commands.add_parser('bundle')
    for key in ('skill', 'tool-root', 'tool', 'category', 'slug'):
        bundler.add_argument('--' + key, required=True)
    finalize = commands.add_parser('finish')
    for key in ('tool-root', 'tool', 'skills-root'):
        finalize.add_argument('--' + key, required=True)
    check = commands.add_parser('check')
    check.add_argument('--tool-root', required=True)
    check.add_argument('--tool', required=True)
    listing = commands.add_parser('destinations')
    for key in ('tool-root', 'tool', 'home', 'project'):
        listing.add_argument('--' + key, required=True)
    args = parser.parse_args()
    if args.command == 'copy-tree':
        copy_tree(args.source, args.destination)
    elif args.command == 'prepare':
        prepare(args.tool_root, args.tool)
    elif args.command == 'bundle':
        bundle(args.skill, args.tool_root, args.tool, args.category, args.slug)
    elif args.command == 'finish':
        finish(args.tool_root, args.tool, args.skills_root)
    elif args.command == 'check':
        inventory(args.tool_root, args.tool)
    else:
        import sys
        data = inventory(args.tool_root, args.tool)
        for record in data['files']:
            for dest in destinations(args.tool, record['path'], args.home, args.project):
                sys.stdout.buffer.write(os.fsencode(str(Path(args.tool_root) / record['path'])) + b'\0' + os.fsencode(str(dest)) + b'\0')


if __name__ == '__main__':
    import sys
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print('[resources] blocked: %s' % exc, file=sys.stderr)
        sys.exit(2)
