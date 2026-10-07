#!/usr/bin/env python3
"""External bounded-loop controller; commands must be owner-approved bounded adapters.

Reserve worst-case calls/tokens/cost BEFORE each dispatch. The adapter must itself
bound internal provider calls and per-call token/monetary liability; this generic
controller cannot meter hidden traffic or make an unbounded command safe.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def frozen_digest(paths):
    digest = hashlib.sha256()
    for value in sorted(paths):
        root = Path(value)
        if not root.exists() or root.is_symlink():
            raise ValueError('missing/symlinked frozen boundary: ' + value)
        entries = [root, *sorted(root.rglob('*'))] if root.is_dir() else [root]
        for path in entries:
            if path.is_symlink():
                raise ValueError('symlinked frozen verifier: ' + str(path))
            digest.update(str(path).encode() + b'\0' + str(path.stat().st_mode).encode() + b'\0')
            if path.is_file():
                data = path.read_bytes()
                digest.update(len(data).to_bytes(8, 'big') + data)
            elif not path.is_dir():
                raise ValueError('unsupported frozen entry: ' + str(path))
    return digest.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    try:
        with temporary.open('x') as out:
            json.dump(value, out, indent=2, allow_nan=False)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_budget(budget):
    if not isinstance(budget, dict):
        raise ValueError('budget must be an object')
    for key in ('max_dispatches', 'max_calls', 'max_tokens', 'max_seconds', 'max_cost_usd',
                'calls_per_dispatch', 'tokens_per_dispatch', 'cost_usd_per_dispatch'):
        value = budget.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('missing/invalid liability: ' + key)
        if 'cost' not in key and 'seconds' not in key and type(value) is not int:
            raise ValueError('counts must be integers: ' + key)
    if budget['max_dispatches'] < 1 or budget['max_seconds'] <= 0:
        raise ValueError('positive dispatch/time bounds required')
    if not isinstance(budget.get('adapter_bound_evidence'), str) or not budget['adapter_bound_evidence'].strip():
        raise ValueError('owner-approved adapter hard-bound evidence required')


def terminate(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    # A parent can exit while its children survive TERM. Always clean its group.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_guarded(command, budget, frozen, state_dir):
    validate_budget(budget)
    if not command or os.name != 'posix':
        raise ValueError('POSIX process-group controller and command required')
    if not isinstance(frozen, dict) or not isinstance(frozen.get('paths'), list) or not frozen['paths']:
        raise ValueError('nonempty frozen verifier manifest required')
    if frozen_digest(frozen['paths']) != frozen.get('sha256'):
        raise ValueError('frozen verifier changed before dispatch')
    state = Path(state_dir)
    state.mkdir(parents=True, exist_ok=True)
    lock = state / 'controller.lock'
    # Never auto-reclaim an existing lock, including one left by a crash.
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    process = None
    receipt = {'status': 'running', 'dispatches': 0, 'reserved_calls': 0,
               'reserved_tokens': 0, 'reserved_cost_usd': 0,
               'verifier_sha256': frozen['sha256'], 'budget': budget,
               'accounting': 'worst-case reservations, never refunds failed dispatches'}
    started = time.monotonic()
    def interrupted(signum, frame):
        raise InterruptedError('controller cancelled by signal ' + str(signum))
    handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        if (state / 'receipt.json').exists():
            raise ValueError('state budget already consumed; a new run/budget requires owner approval')
        for _ in range(budget['max_dispatches']):
            if time.monotonic() - started >= budget['max_seconds']:
                receipt['status'] = 'budget_exceeded'
                break
            if frozen_digest(frozen['paths']) != frozen['sha256']:
                receipt['status'] = 'verifier_changed'
                break
            reservations = {field: receipt['reserved_' + field] + budget[field + '_per_dispatch']
                            for field in ('calls', 'tokens', 'cost_usd')}
            if any(value > budget['max_' + field] for field, value in reservations.items()):
                receipt['status'] = 'budget_exceeded'
                break
            receipt.update({'reserved_' + k: v for k, v in reservations.items()})
            receipt['dispatches'] += 1
            save(state / 'receipt.json', receipt)
            process = subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL)
            while process.poll() is None:
                if time.monotonic() - started >= budget['max_seconds']:
                    receipt['status'] = 'budget_exceeded'
                    break
                if frozen_digest(frozen['paths']) != frozen['sha256']:
                    receipt['status'] = 'verifier_changed'
                    break
                time.sleep(0.05)
            if receipt['status'] != 'running':
                terminate(process)
                break
            code = process.wait()
            terminate(process)  # no orphaned background processes on success/failure
            if frozen_digest(frozen['paths']) != frozen['sha256']:
                receipt['status'] = 'verifier_changed'
                break
            if code != 0:
                receipt.update(status='execution_error', exit_code=code)
                break
        else:
            receipt['status'] = 'completed_dispatches'
    except (OSError, ValueError, InterruptedError) as exc:
        receipt.update(status='blocked', error=str(exc))
    finally:
        if process:
            terminate(process)
        receipt['seconds'] = time.monotonic() - started
        # A refused restart must not erase the original consumed liability.
        if receipt['dispatches'] or not (state / 'receipt.json').exists():
            save(state / 'receipt.json', receipt)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        lock.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    freeze = commands.add_parser('freeze', help='owner/reviewer-approved freeze before a run')
    freeze.add_argument('--output', type=Path, required=True)
    freeze.add_argument('paths', nargs='+')
    run = commands.add_parser('run')
    run.add_argument('--budget', type=Path, required=True)
    run.add_argument('--frozen', type=Path, required=True)
    run.add_argument('--state-dir', type=Path, required=True)
    run.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.mode == 'freeze':
            paths = [str(Path(p).absolute()) for p in args.paths]
            if args.output.exists():
                raise ValueError('freeze receipt exists; reviewer must approve a NEW manifest, never overwrite')
            value = {'paths': paths, 'sha256': frozen_digest(paths)}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x') as out:
                json.dump(value, out, indent=2)
            return 0
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        receipt = run_guarded(command, json.loads(args.budget.read_text()), json.loads(args.frozen.read_text()), args.state_dir)
        print(json.dumps(receipt, indent=2))
        return 0 if receipt['status'] == 'completed_dispatches' else 2
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'status': 'blocked', 'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
