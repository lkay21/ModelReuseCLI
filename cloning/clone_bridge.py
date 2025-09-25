import subprocess
import os
import logging

logger = logging.getLogger('cli_logger')


def clone_with_isogit(repo_url: str, local_dir: str = "./models") -> None:
    os.makedirs(local_dir, exist_ok=True)
    logger.debug(f"Cloning {repo_url} into {local_dir} using isogit...")
    result = subprocess.run(
        ["node", str(script_path), repo_url, local_dir_abs],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Clone failed:\n{result.stderr}")
        raise Exception(f"Clone failed: {result.stderr}")
    logger.info(f"Successfully cloned {repo_url} into {local_dir}.")


# For testing purposes only - delete upon integration
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("Usage: python clone_bridge.py <repo_url> [local_dir]")
#         sys.exit(1)

#     repo_url = sys.argv[1]
#     local_dir = sys.argv[2] if len(sys.argv) > 2 else "./models"

#     try:
#         clone_with_isogit(repo_url, local_dir)
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     print("Clone completed successfully.")
