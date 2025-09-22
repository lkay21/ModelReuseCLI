from __future__ import annotations
import subprocess, sys
from pathlib import Path
from typing import Tuple
from cloning.clone_bridge import clone_with_isogit  # keep this if you pass URLs

def _ensure_flake8() -> None:
    try:
        import flake8  
    except Exception:
        print("flake8 required: pip install flake8", file=sys.stderr)
        raise

def _run_flake8_count(repo_dir: Path) -> Tuple[int, str]:
    _ensure_flake8()
    proc = subprocess.run(["flake8", str(repo_dir), "--count", "--statistics"],
                          capture_output=True, text=True)
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    errors = 0
    for line in out.strip().splitlines()[::-1]:
        s = line.strip()
        if s.isdigit():
            errors = int(s); break
    return errors, out

def _lint_score(errors: int) -> float:
    cap = 100  # 0 errs -> 1.0; 100+ errs -> ~0.0
    return max(0.0, 1.0 - min(1.0, errors / cap))

def code_quality(target: str, *, clone_root: str = "./models") -> float:
    p = Path(target)
    if p.exists() and p.is_dir():
        repo_dir = p
    else:
        clone_with_isogit(target, clone_root)             # clone URL on demand
        name = target.rstrip("/").split("/")[-1].replace(".git", "")
        repo_dir = Path(clone_root) / name
    errors, _ = _run_flake8_count(repo_dir)
    return _lint_score(errors)
