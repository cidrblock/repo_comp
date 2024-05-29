"""Check the tox.ini file."""

import difflib
import shutil

from repo_comp.config import Config
from repo_comp.utils import (
    ask_yes_no,
    get_commit_msg,
    load_txt_file,
    path_to_data_file,
    render_diff,
    subprocess_run,
)


def run(config: Config) -> None:
    """Run the check.

    Args:
        config: The configuration data.
    """
    tox_init = path_to_data_file("tox.ini")
    base_content = load_txt_file(tox_init).splitlines()
    commit_msg = ""
    for repo in config.repos:
        config.output.info(f"[{repo.name}] Checking tox.ini...")
        repo_file = repo.work_dir.joinpath("tox.ini")
        repo_content = repo_file.read_text().splitlines()
        if base_content == repo_content:
            config.output.info(f"[{repo.name}] tox.ini in is correct.")
            continue
        diff = difflib.unified_diff(
            base_content,
            repo_content,
            n=5,
            fromfile="base",
            tofile="repo",
        )
        render_diff(diff)
        do_update = ask_yes_no(
            f"Do you want to update the tox.ini file in {repo.name}?",
        )
        if not do_update:
            continue
        if not commit_msg:
            commit_msg, commit_text_file = get_commit_msg(
                config=config,
                commit_msg=commit_msg,
            )
        else:
            reuse_commit = ask_yes_no("Do you want to reuse the commit message?")
            if not reuse_commit:
                commit_msg, commit_text_file = get_commit_msg(
                    config=config,
                    commit_msg=commit_msg,
                )

        new_branch = f"chore/tox_init_{config.session_id}"
        command = f"git checkout -t -b {new_branch}"
        msg = f"[{repo.name}] Creating a new tracking branch {new_branch}..."
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        shutil.copy(tox_init, repo_file)
        config.output.info(f"[{repo.name}] Updated tox.ini.")

        command = "git add tox.ini"
        msg = f"[{repo.name}] Staging changes..."
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        command = f"git commit --file {commit_text_file}"
        msg = f"[{repo.name}] Committing changes..."
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        command = f"git push origin {new_branch}"
        msg = f"[{repo.name}] Pushing changes to origin..."
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        title = "chore: Update tox.ini"
        command = (
            f'gh pr create --repo {repo.upstream} --title "{title}"'
            f" --base main --head {repo.origin_owner}:{new_branch} --body-file {commit_text_file}"
        )
        msg = f"[{repo.name}] Creating PR..."
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        config.output.info(f"[{repo.name}] PR created.")
