import shutil
import subprocess
import tempfile

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
