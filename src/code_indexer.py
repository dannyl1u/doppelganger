import os
import tempfile
import subprocess
import shutil
from typing import List, Dict
from src.github_api import get_access_token


def clone_repo_branch(
    installation_id: str, repo_full_name: str, branch: str = "main"
) -> str:
    """Clone specific branch of repository to temporary directory"""

    temp_dir = tempfile.mkdtemp()
    access_token = get_access_token(installation_id)
    clone_url = f"https://x-access-token:{access_token}@github.com/{repo_full_name}.git"
    try:
        subprocess.run(
            ["git", "clone", "-b", branch, "--single-branch", clone_url, temp_dir],
            check=True,
        )
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)  # Clean up on error
        raise e


def index_code_files(temp_dir: str) -> List[Dict[str, str]]:
    """Index all code files from a directory"""
    code_files = []

    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.startswith(".") or "node_modules" in root:
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, temp_dir)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                code_files.append({"path": relative_path, "content": content})
            except UnicodeDecodeError:
                continue  # Skip binary files

    return code_files
