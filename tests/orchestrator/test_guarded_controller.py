"""No provider calls: exercise external controller using bounded local commands."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'skills/loops/loop-controller/scripts/run_guarded.py'


def setup(tmp_path, **limits):
    verifier = tmp_path / 'verifier.txt'
    verifier.write_text('frozen assertion\n')
    frozen = tmp_path / 'frozen.json'
    subprocess.run([sys.executable, str(CLI), 'freeze', '--output', str(frozen), str(verifier)], check=True)
    budget = dict(max_dispatches=2, max_calls=2, max_tokens=20, max_seconds=5,
                  max_cost_usd=0, calls_per_dispatch=1, tokens_per_dispatch=10,
                  cost_usd_per_dispatch=0, adapter_bound_evidence='local test command has no network')
    budget.update(limits)
    filename = tmp_path / 'budget.json'
    filename.write_text(json.dumps(budget))
    state = tmp_path / 'state'
    command = [sys.executable, str(CLI), 'run', '--budget', str(filename),
               '--frozen', str(frozen), '--state-dir', str(state), '--']
    return command, state, verifier


def test_reservation_caps_before_dispatch(tmp_path):
    command, state, _ = setup(tmp_path, max_calls=1)
    target = tmp_path / 'dispatched.txt'
    script = f'from pathlib import Path; p=Path({str(target)!r}); p.write_text(p.read_text()+"x" if p.exists() else "x")'
    result = subprocess.run(command + [sys.executable, '-c', script], capture_output=True, text=True)
    assert result.returncode == 2 and target.read_text() == 'x'
    receipt = json.loads((state / 'receipt.json').read_text())
    assert receipt['status'] == 'budget_exceeded' and receipt['reserved_calls'] == 1
    assert receipt['reserved_tokens'] == 10 and not (state / 'controller.lock').exists()


def test_success_and_failure_receipts(tmp_path):
    command, state, _ = setup(tmp_path)
    result = subprocess.run(command + [sys.executable, '-c', 'pass'], capture_output=True, text=True)
    assert result.returncode == 0
    receipt = json.loads((state / 'receipt.json').read_text())
    assert receipt['dispatches'] == 2 and receipt['reserved_calls'] == 2
    retry = subprocess.run(command + [sys.executable, '-c', 'pass'], capture_output=True, text=True)
    assert retry.returncode == 2  # restarting must not reset consumed budget


def test_changed_verifier_stops_before_next_dispatch(tmp_path):
    command, state, verifier = setup(tmp_path)
    result = subprocess.run(command + [sys.executable, '-c', f'from pathlib import Path; Path({str(verifier)!r}).write_text("weakened")'], capture_output=True, text=True)
    assert result.returncode == 2
    receipt = json.loads((state / 'receipt.json').read_text())
    assert receipt['status'] == 'verifier_changed' and receipt['dispatches'] == 1


def test_timeout_kills_process_group(tmp_path):
    command, state, _ = setup(tmp_path, max_seconds=.25)
    marker = tmp_path / 'orphan.txt'
    child = f'import time; from pathlib import Path; time.sleep(1.5); Path({str(marker)!r}).write_text("orphan")'
    parent = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(10)'
    started = time.monotonic()
    result = subprocess.run(command + [sys.executable, '-c', parent], capture_output=True, text=True, timeout=4)
    assert result.returncode == 2 and time.monotonic() - started < 3
    assert json.loads((state / 'receipt.json').read_text())['status'] == 'budget_exceeded'
    time.sleep(1.6)
    assert not marker.exists()


def test_existing_lock_and_stale_freeze_block(tmp_path):
    command, state, verifier = setup(tmp_path)
    state.mkdir()
    (state / 'controller.lock').write_text('another owner')
    result = subprocess.run(command + [sys.executable, '-c', 'pass'], capture_output=True, text=True)
    assert result.returncode == 2 and (state / 'controller.lock').read_text() == 'another owner'
    (state / 'controller.lock').unlink()
    verifier.write_text('changed before dispatch')
    result = subprocess.run(command + [sys.executable, '-c', 'pass'], capture_output=True, text=True)
    assert result.returncode == 2 and not (state / 'receipt.json').exists()


def test_unknown_liability_refused(tmp_path):
    command, state, _ = setup(tmp_path, cost_usd_per_dispatch=None)
    result = subprocess.run(command + [sys.executable, '-c', 'pass'], capture_output=True, text=True)
    assert result.returncode == 2 and not (state / 'receipt.json').exists()
