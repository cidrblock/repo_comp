"""The cli entrypoint for the repo_comp package."""

import os
import shutil

from repo_comp.args import parse_args
from repo_comp.checks import tox_ini
from repo_comp.config import Config
from repo_comp.output import Output, TermFeatures
from repo_comp.repo import Repo
from repo_comp.utils import load_toml_file, path_to_data_file, subprocess_run, tmp_path


def fork_clone_all(config: Config) -> None:
    """Fork all the repositories."""
    for repo in config.repos:
        if config.args.cf:
            command = f"gh repo clone {repo.upstream_uri} -- --depth=1"
            msg = f"[{repo.name}] Cloning from upstream..."
            subprocess_run(
                command=command,
                cwd=config.tmp_path,
                msg=msg,
                output=config.output,
                verbose=config.args.verbose,
            )

            command = "gh repo fork --remote=False"
            msg = f"[{repo.name}] Ensuring fork is available..."
            subprocess_run(
                command=command,
                cwd=config.tmp_path.joinpath(repo.name),
                msg=msg,
                output=config.output,
                verbose=config.args.verbose,
            )

            shutil.rmtree(config.tmp_path.joinpath(repo.name))

        msg = f"[{repo.name}] Cloning from origin..."
        command = f"gh repo clone {repo.origin_uri} -- --depth=1"
        subprocess_run(
            command=command,
            cwd=config.tmp_path,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )

        repo.work_dir = config.tmp_path.joinpath(repo.name)

        msg = f"[{repo.name}] Resetting to upstream/main..."
        command = "git reset --hard upstream/main"
        subprocess_run(
            command=command,
            cwd=repo.work_dir,
            msg=msg,
            output=config.output,
            verbose=config.args.verbose,
        )


def main() -> None:
    """Load the configuration data file."""
    args = parse_args()
    term_features = TermFeatures(
        color=False if os.environ.get("NO_COLOR") else not args.no_ansi,
        links=not args.no_ansi,
    )
    output = Output(
        log_file=args.log_file,
        log_level=args.log_level,
        log_append=args.log_append,
        term_features=term_features,
        verbosity=args.verbose,
    )

    data_file = path_to_data_file("repos.toml")
    repos = load_toml_file(data_file)
    _tmp_path = tmp_path()
    output.info(f"Using temporary directory {_tmp_path}")
    repo_list = [Repo(name=k, **v[0]) for k, v in repos["repos"].items()]
    editor = os.environ.get("EDITOR", "vi")
    config = Config(
        args=args,
        editor=editor,
        output=output,
        repos=repo_list,
        tmp_path=_tmp_path,
    )
    output.info(f"The current session ID is {config.session_id}.")
    fork_clone_all(config)
    tox_ini.run(config)


if __name__ == "__main__":
    main()
