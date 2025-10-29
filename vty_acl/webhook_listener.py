import json
import subprocess
from pathlib import Path
from typing import Tuple, Optional

from fastapi import FastAPI, Header, BackgroundTasks
from fastapi.responses import PlainTextResponse
from generator import main as vty_acl_generator


REPO_NAME="config_templates"
REPO_URL = "https://github.com/Akellazzz/config_templates.git"
DEFAULT_BRANCH = "develop"
# Path to repo is now one level up since we're in vty_acl/
DEST_DIR = (Path(__file__).resolve().parent.parent / REPO_NAME).as_posix()

def _run_git_command(args: list[str]) -> None:
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stdout}")
    if result.stdout:
        print(result.stdout.strip())


def _get_current_commit_id(repo_path: Path) -> str:
    """Get the short commit ID from the current HEAD."""
    result = subprocess.run(
        ["git", "-C", repo_path.as_posix(), "rev-parse", "--short", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get commit ID: {result.stdout}")
    return result.stdout.strip()


def sync_repo(repo_url: str = REPO_URL, branch: str = DEFAULT_BRANCH, dest_dir: str = DEST_DIR) -> Path:
    dest_path = Path(dest_dir)
    try:
        if (dest_path / ".git").exists():
            print(f"Syncing existing repo at {dest_path}...")
            _run_git_command(["git", "-C", dest_path.as_posix(), "fetch", "origin", "--prune"])
            _run_git_command(["git", "-C", dest_path.as_posix(), "checkout", branch])
            _run_git_command(["git", "-C", dest_path.as_posix(), "reset", "--hard", f"origin/{branch}"])
        else:
            if not dest_path.exists():
                dest_path.mkdir(parents=True, exist_ok=True)
            print(f"Cloning {repo_url} (branch {branch}) into {dest_path}...")
            _run_git_command([
                "git",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--branch",
                branch,
                repo_url,
                dest_path.as_posix(),
            ])
    except Exception as exc:
        print(f"Repository sync failed: {exc}")
        raise
    return dest_path


def create_release_candidate_branch(repo_path: Path, commit_id: str) -> None:
    """Create a release candidate branch, commit changes, and push to remote."""
    branch_name = f"release_candidate_{commit_id}"
    
    try:
        # Check if there are any changes to commit
        result = subprocess.run(
            ["git", "-C", repo_path.as_posix(), "diff", "--quiet", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        has_changes = result.returncode != 0
        
        if not has_changes:
            print("No changes to commit, skipping release candidate creation")
            return
        
        # Create and checkout new branch
        print(f"Creating branch {branch_name}...")
        _run_git_command(["git", "-C", repo_path.as_posix(), "checkout", "-b", branch_name])
        
        # Add all changes
        print("Adding changes...")
        _run_git_command(["git", "-C", repo_path.as_posix(), "add", "-A"])
        
        # Commit changes
        print("Committing changes...")
        _run_git_command([
            "git",
            "-C",
            repo_path.as_posix(),
            "commit",
            "-m",
            f"Release candidate from commit {commit_id}",
        ])
        
        # Push to remote
        print(f"Pushing {branch_name} to remote...")
        _run_git_command(["git", "-C", repo_path.as_posix(), "push", "origin", branch_name])
        
        print(f"Release candidate branch {branch_name} created and pushed successfully")
        
    except Exception as exc:
        print(f"Failed to create release candidate branch: {exc}")
        raise


def trigger_generation() -> None:
    try:
        repo_path = sync_repo()
        print(f"Repository ready at {repo_path}. Starting generation...")
        
        # Get commit ID before generation
        commit_id = _get_current_commit_id(repo_path)
        print(f"Current commit ID: {commit_id}")
        
        vty_acl_generator()
        
        print("Generation finished successfully")
        
        # Create release candidate branch after successful generation
        create_release_candidate_branch(repo_path, commit_id)
        
    except Exception as exc:
        print(f"Generation failed: {exc}")


app = FastAPI()


@app.post("/webhook", response_class=PlainTextResponse)
async def webhook(
    background_tasks: BackgroundTasks,
    payload: Optional[dict] = None,
    x_gitlab_event: Optional[str] = Header(default=None, alias="X-Gitlab-Event"),
    x_github_event: Optional[str] = Header(default=None, alias="X-GitHub-Event"),
):
    is_git_event = bool(x_gitlab_event or x_github_event)
    if not is_git_event:
        return PlainTextResponse("Ignored\n", status_code=202)

    ref = None
    if isinstance(payload, dict):
        ref = payload.get("ref")

    if ref and ref not in (f"refs/heads/{DEFAULT_BRANCH}", DEFAULT_BRANCH):
        return PlainTextResponse("Ignored (non-main branch)\n", status_code=202)

    background_tasks.add_task(trigger_generation)
    return PlainTextResponse("OK\n", status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook_listener:app", host="0.0.0.0", port=8080, reload=False)

"""
curl -X POST http://localhost:8080/webhook \
  -H 'Content-Type: application/json' \
  -H 'X-Gitlab-Event: Push Hook' \
  -d '{"ref":"refs/heads/develop"}'
"""

