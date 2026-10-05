"""CC/Cursor skill-directory sync; do not infer additional host support."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

from resource_delivery import (MANIFEST, RUNTIME, atomic_json, bundle, contained,
                               discover, file_record, resource_files, selected)


def tree_hash(path):
    import hashlib
    h = hashlib.sha256()
    for p in sorted(Path(path).rglob('*')):
        if p.is_symlink():
            raise ValueError('unowned symlink in sync copy: ' + str(p))
        if p.is_file():
            h.update(str(p.relative_to(path)).encode())
            record = file_record(p)
            h.update(json.dumps(record, sort_keys=True).encode())
    return h.hexdigest()


def pull_skills(args, repo, definitions):
    sources = [t for t in definitions if args.from_all or (args.from_claude if t == 'claude-code' else args.from_cursor)]
    pending = []
    for tool in sources:
        base = definitions[tool]
        if not base.exists():
            continue
        for source in sorted(set(base.glob('*/SKILL.md')) | set(base.glob('*/*/SKILL.md'))):
            slug = source.parent.name
            if args.targets and slug not in args.targets and source.parent.parent.name not in args.targets:
                continue
            if source.resolve().is_relative_to(repo):
                continue
            resource_files(source.parent)
            match = next((p.parent for p, _, s in discover(repo / 'skills') if s == slug), None)
            # New imports live in a real category, never skills/<slug> accidentally.
            dest = match or repo / 'skills/workflows' / slug
            contained(dest / '.boundary-check', repo)
            if dest.exists() and not args.replace_with_backup:
                raise ValueError('pull collision: %s; explicit --replace-with-backup required' % dest)
            pending.append((source, dest))
    if len({str(d) for _, d in pending}) != len(pending):
        raise ValueError('multiple imports target the same skill; select one source')
    for source, dest in pending:
        print('%spull: %s -> %s' % ('[dry-run] ' if args.dry_run else '', source.parent, dest))
        if args.dry_run:
            continue
        if dest.exists():
            dest.rename(dest.with_name(dest.name + '.ats-backup-' + uuid.uuid4().hex))
        dest.mkdir(parents=True)
        shutil.copy2(source, dest / 'SKILL.md')
        for file in resource_files(source.parent):
            target = dest / file.relative_to(source.parent)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    modes = parser.add_mutually_exclusive_group()
    for flag in ('link', 'copy', 'unlink', 'status', 'clean'):
        modes.add_argument('--' + flag, action='store_true')
    for flag in ('to-claude', 'to-cursor', 'to-all', 'from-claude', 'from-cursor', 'from-all'):
        parser.add_argument('--' + flag, action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--replace-with-backup', action='store_true', help='explicit approval to back up an unowned/edited collision before replacing it')
    parser.add_argument('targets', nargs='*')
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    home = Path.home()
    definitions = {'claude-code': home / '.claude/skills', 'cursor': home / '.cursor/skills-cursor'}
    tools = [t for t in definitions if args.to_all or (args.to_claude if t == 'claude-code' else args.to_cursor)]
    if args.status or args.clean:
        tools = tools or list(definitions)
    pull = args.from_all or args.from_claude or args.from_cursor
    if pull:
        return pull_skills(args, repo, definitions)
    if not tools:
        raise ValueError('specify --to-claude/--to-cursor/--to-all or --status/--clean')
    inventory = discover(repo / 'skills')
    known = {s for _, _, s in inventory} | {c for _, c, _ in inventory} | {c + '/' + s for _, c, s in inventory}
    if any(t not in known for t in args.targets):
        raise ValueError('unknown category/skill selection')
    changes = []
    receipts = {}
    for tool in tools:
        base = definitions[tool]
        receipt = base / '.ats-sync-owned.json'
        if receipt.is_symlink():
            raise ValueError('symlinked sync receipt')
        state = json.loads(receipt.read_text()) if receipt.exists() else {'schema_version': 1, 'repo': str(repo), 'entries': {}}
        if state.get('schema_version') != 1 or state.get('repo') != str(repo):
            raise ValueError('sync ownership belongs to another checkout; reconcile explicitly')
        receipts[receipt] = state
        entries = state['entries']
        if not isinstance(entries, dict) or any('/' in n or n in ('.', '..') for n in entries):
            raise ValueError('invalid ownership entries')
        if args.clean or args.unlink:
            for name, record in list(entries.items()):
                if args.targets and not selected(record['category'], name, args.targets):
                    continue
                dest = base / name
                contained(dest.parent / (name + '.boundary-check'), home)
                if dest.is_symlink() and os.readlink(dest) == record.get('target') and (args.unlink or not dest.exists()):
                    changes.append(('unlink', dest, None, receipt, name, record))
            continue
        for source, category, slug in inventory:
            if not selected(category, slug, args.targets):
                continue
            # Capability resolution projection; native CC retains everything,
            # Cursor and non-CC targets resolve required capabilities/flags.
            if tool != 'claude-code':
                from capability_resolver import parse_frontmatter, resolve_skill_execution
                fm = parse_frontmatter(source)
                res = resolve_skill_execution(fm, tool)
                if res.get('status') != 'ALLOWED':
                    continue
            dest = base / slug
            # Leaf symlink intentionally managed here; parents must not redirect.
            contained(dest.parent / (slug + '.boundary-check'), home)
            owned = entries.get(slug)
            same_link = dest.is_symlink() and os.readlink(dest) == str(source.parent)
            exists = dest.exists() or dest.is_symlink()
            if args.status:
                print('%s/%s: %s' % (tool, slug, 'linked' if same_link else 'owned copy' if owned else 'unowned collision' if exists else 'missing'))
                continue
            if same_link and not args.copy:
                # Exact source link is safe to adopt; never remove arbitrary links.
                changes.append(('adopt', dest, source, receipt, slug, {'category': category, 'target': str(source.parent), 'kind': 'link'}))
                continue
            trusted = owned and ((dest.is_symlink() and os.readlink(dest) == owned.get('target')) or
                                  (dest.is_dir() and not dest.is_symlink() and owned.get('kind') == 'copy' and tree_hash(dest) == owned.get('sha256')))
            if exists and not trusted and not args.replace_with_backup:
                raise ValueError('unowned/edited collision: %s; preview and approve --replace-with-backup' % dest)
            changes.append(('copy' if args.copy else 'link', dest, source, receipt, slug,
                            {'category': category, 'backup': bool(exists and not trusted)}))
    # Validate all collisions before the first write; dry run never records state.
    for action, dest, source, receipt, slug, record in changes:
        print('%s%s: %s' % ('[dry-run] ' if args.dry_run else '', action, dest))
    if args.dry_run or args.status:
        return
    for action, dest, source, receipt, slug, record in changes:
        entries = receipts[receipt]['entries']
        if action == 'adopt':
            entries[slug] = record
            continue
        if action == 'unlink':
            dest.unlink()
            entries.pop(slug, None)
            continue
        if record.get('backup'):
            backup = dest.with_name(dest.name + '.ats-backup-' + uuid.uuid4().hex)
            dest.rename(backup)
            print('backup: ' + str(backup))
        elif action == 'link' and dest.is_symlink():
            dest.unlink()
        elif action == 'link' and dest.exists():
            shutil.rmtree(dest)  # only a validated byte-identical owned copy
        dest.parent.mkdir(parents=True, exist_ok=True)
        if action == 'link':
            dest.symlink_to(source.parent, target_is_directory=True)
            entries[slug] = {'category': record['category'], 'kind': 'link', 'target': str(source.parent)}
        else:
            # Native skill-directory adapter uses canonical prompt, filtered
            # resources and the same runtime contract as converted exports.
            with tempfile.TemporaryDirectory(prefix='.ats-sync-', dir=str(dest.parent)) as temp:
                staging = Path(temp)
                root_rel = record['category'] + '/' + slug
                prompt = staging / root_rel / 'SKILL.md'
                prompt.parent.mkdir(parents=True)
                shutil.copy2(source, prompt)
                bundle(source, staging, 'claude-code', record['category'], slug)
                saved = None
                if dest.is_symlink() or dest.exists():
                    saved = dest.with_name(dest.name + '.ats-previous-' + uuid.uuid4().hex)
                    dest.rename(saved)
                try:
                    os.replace(prompt.parent, dest)
                except Exception:
                    if saved: saved.rename(dest)
                    raise
                if saved:
                    if saved.is_symlink(): saved.unlink()
                    else: shutil.rmtree(saved)
            entries[slug] = {'category': record['category'], 'kind': 'copy', 'sha256': tree_hash(dest)}
    for receipt, state in receipts.items():
        if changes:
            atomic_json(receipt, state)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print('sync blocked: %s' % exc, file=sys.stderr)
        sys.exit(2)
