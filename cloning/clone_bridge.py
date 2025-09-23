import subprocess
import os
from pathlib import Path

def clone_with_isogit(repo_url: str, local_dir: str = "./models") -> None:
    os.makedirs(local_dir, exist_ok=True)

    # Resolve absolute path to cloning/clone.js 
    script_path = Path(__file__).resolve().with_name("clone.js")

    if not script_path.exists():
        raise RuntimeError(f"clone.js not found at: {script_path}")

    # Run Node with an absolute path; set cwd to the cloning/ folder
    result = subprocess.run(
        ["node", str(script_path), repo_url, local_dir],
        capture_output=True,
        text=True,
        cwd=str(script_path.parent),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Clone failed:\n{result.stderr.strip()}")
    if result.stdout:
        print(result.stdout.strip())  # optional



# For testing purposes only - delete upon integration
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cloning/clone_bridge.py <repo_url> [local_dir]")
        sys.exit(1)

    repo_url = sys.argv[1]
    local_dir = sys.argv[2] if len(sys.argv) > 2 else "./models"

    try:
        clone_with_isogit(repo_url, local_dir)
    except Exception as e:
        print(e)
        sys.exit(1)
    print("Clone completed successfully.")

