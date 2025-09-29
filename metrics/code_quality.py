from __future__ import annotations

import os
import ast
import subprocess
import sys
from pathlib import Path

from cloning.clone_bridge import clone_with_isogit  

import logging
logger = logging.getLogger('cli_logger')


def _ensure_flake8() -> None:
    try:
        subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("flake8 required. Try: pip install flake8")
        raise FileNotFoundError("flake8 not found. Please install it via 'pip install flake8'.")

def _simple_lint_check(repo_dir: Path) -> tuple[int, int]:
    _ensure_flake8()
    
    # Get Python files with basic exclusions
    exclude_dirs = {"examples", "tests", "test", "docs", "__pycache__", ".git", "build", "dist"}
    py_files = []
    
    for f in repo_dir.rglob("*.py"):
        if len(py_files) >= 100:  # Stop searching after 100 files found
            break
        if not any(part in exclude_dirs for part in f.parts):
            py_files.append(f)
        
    sample_files = py_files[:25]
    if not sample_files:
        return 0, 0
    
    # Run flake8 with basic config and timeout
    file_args = [str(f.relative_to(repo_dir)) for f in sample_files]
    
    try:
        proc = subprocess.run(
            [
                sys.executable, "-m", "flake8", 
                *file_args, 
                "--count",
                "--max-line-length=128",
                "--ignore=E501,W503,E203"
            ],
            capture_output=True,
            text=True,
            cwd=repo_dir,
            timeout=30
        )
        
        # Extract error count
        for line in reversed((proc.stdout or "").strip().splitlines()):
            if line.strip().isdigit():
                return int(line.strip()), len(sample_files)
        return 0, len(sample_files)
        
    except subprocess.TimeoutExpired:
        logger.error(f"  Lint timeout, skipping", file=sys.stderr)
        return 0, 0


def _lint_score(errors: int, num_files: int) -> float:
    # cap = 100  # Fixed cap like original implementation
    # return max(0.0, 1.0 - min(1.0, errors / cap))
    if num_files == 0:
        return 1.0  # no python to lint, technically perfect score

    ERRORS_PER_FILE_CAP = 50
    
    errors_per_file = errors / num_files
    
    # Linearly scale the score down from 1.0 to 0.0 based on error density.
    score = 1.0 - (errors_per_file / ERRORS_PER_FILE_CAP)
    
    return .5 * max(0.0, score)



# Purdue GenAI naming subscore ([0, 0.5]) using AST variable names
def _collect_var_names(repo_dir: Path, max_files: int = 10) -> list[str]:
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


def _maybe_purdue_genai_naming(repo_dir: Path) -> float | None:
    try:
        from apis.purdue_genai import get_purdue_genai_key, prompt_purdue_genai
        key = get_purdue_genai_key()
    except Exception:
        key = None
        prompt_purdue_genai = None  

    if not (key and prompt_purdue_genai):
        return None

    var_names = _collect_var_names(repo_dir)
    if not var_names:
        return None

    prompt = (
        "Rate Python variable naming quality (clarity, descriptiveness, snake_case, "
        "avoiding cryptic names). Return ONLY a float in [0,0.5].\n\n"
        f"Variables (sample): {var_names}\n\nJust the number:"
    )
    txt = (prompt_purdue_genai(prompt, key) or "").strip()
    for tok in txt.replace(",", " ").split():
        try:
            val = float(tok)
            return max(0.0, min(0.5, val))
        except Exception:
            continue
    return None

def code_quality(target: str, code_type: str) -> float:
    """
    Returns float in [0,1].
      - Lint score from flake8 maps to [0,1].
      - If Purdue GenAI key is present, blend variable-naming subscore ([0,0.5]):
            score = 0.5 * lint + naming
        Else, return lint-only (offline-friendly).
    """
    clone_root: str = "./models"
    if(code_type != "github"):
        return 0.1
    p = Path(target)
    if p.exists() and p.is_dir():
        repo_dir = p
    else:
        clone_with_isogit(target, clone_root)
        name = target.rstrip("/").split("/")[-1].replace(".git", "")
        repo_dir = Path(clone_root) / name

    num_errors, files_checked = _simple_lint_check(repo_dir)
    logger.debug(f"  Found {num_errors} linting errors in {files_checked} files for {target}")
    lint01 = _lint_score(num_errors, files_checked)
    naming05 = _maybe_purdue_genai_naming(repo_dir)
    if naming05 is None:
        logger.debug(f"  Using lint-only score: {lint01:.3f}")
        return 2 * lint01

    return max(0.0, min(1.0, lint01 + naming05))
