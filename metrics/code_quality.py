from __future__ import annotations

import os
import ast
import subprocess
import sys
from pathlib import Path

from cloning.clone_bridge import clone_with_isogit  

def _ensure_flake8() -> None:
    try:
        subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("flake8 required. Try: pip install flake8", file=sys.stderr)
        raise


def _run_flake8_count(repo_dir: Path) -> int:
    _ensure_flake8()
    proc = subprocess.run(
        [sys.executable, "-m", "flake8", str(repo_dir), "--count", "--statistics"],
        capture_output=True,
        text=True,
    )
    errors = 0
    for line in reversed((proc.stdout or "").strip().splitlines()):
        s = line.strip()
        if s.isdigit():
            errors = int(s)
            break
    return errors


def _lint_score(errors: int) -> float:
    cap = 100  
    return max(0.0, 1.0 - min(1.0, errors / cap))


# Gemini naming subscore ([0, 0.5]) using AST variable names
def _collect_var_names(repo_dir: Path, max_files: int = 30) -> list[str]:
    names: list[str] = []
    for f in list(repo_dir.rglob("*.py"))[:max_files]:
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.extend(a.arg for a in node.args.args)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names.append(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.append(node.target.id)
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                names.append(node.target.id)
    return names[:200]


def _maybe_gemini_naming(repo_dir: Path) -> float | None:
    try:
        from apis.gemini import get_gemini_key, prompt_gemini
        key = get_gemini_key() or os.getenv("GEMINI_API_KEY")
    except Exception:
        key = os.getenv("GEMINI_API_KEY")
        prompt_gemini = None  

    if not (key and prompt_gemini):
        return None

    var_names = _collect_var_names(repo_dir)
    if not var_names:
        return None

    prompt = (
        "Rate Python variable naming quality (clarity, descriptiveness, snake_case, "
        "avoiding cryptic names). Return ONLY a float in [0,0.5].\n\n"
        f"Variables (sample): {var_names}\n\nJust the number:"
    )
    txt = (prompt_gemini(prompt, key) or "").strip()
    for tok in txt.replace(",", " ").split():
        try:
            val = float(tok)
            return max(0.0, min(0.5, val))
        except Exception:
            continue
    return None

def code_quality(target: str, *, clone_root: str = "./models") -> float:
    """
    Returns float in [0,1].
      - Lint score from flake8 maps to [0,1].
      - If Gemini key is present, blend variable-naming subscore ([0,0.5]):
            score = 0.5 * lint + naming
        Else, return lint-only (offline-friendly).
    """
    p = Path(target)
    if p.exists() and p.is_dir():
        repo_dir = p
    else:
        clone_with_isogit(target, clone_root)
        name = target.rstrip("/").split("/")[-1].replace(".git", "")
        repo_dir = Path(clone_root) / name

    lint01 = _lint_score(_run_flake8_count(repo_dir))
    naming05 = _maybe_gemini_naming(repo_dir)
    if naming05 is None:
        return lint01
    return max(0.0, min(1.0, 0.5 * lint01 + naming05))

