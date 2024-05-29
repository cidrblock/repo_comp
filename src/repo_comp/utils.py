"""Utilities for repo_comp."""

from __future__ import annotations

import importlib.resources
import itertools
import logging
import subprocess
import sys
import tempfile
import threading
import time

from pathlib import Path
from typing import TYPE_CHECKING

import subprocess_tee
import tomllib

from repo_comp.output import Color, Output, TermFeatures


if TYPE_CHECKING:
    import difflib

    from types import TracebackType

    from repo_comp.config import Config

    from .output import Output


logger = logging.getLogger(__name__)


def load_txt_file(file_path: Path) -> str:
    """Load a text file.

    Args:
        file_path: The path to the text file.
    """
    with file_path.open(mode="r") as f:
        return f.read()


def load_toml_file(file_path: Path) -> dict:
    """Load a TOML file.

    Args:
        file_path: The path to the TOML file.
    """
    with file_path.open(mode="rb") as f:
        return tomllib.load(f)


def path_to_data_file(name: str) -> Path:
    """Return the path to a data file.

    Args:
        name: The name of the data file.

    Returns:
        The path to the data file.
    """
    data_dir = importlib.resources.files("repo_comp").joinpath("data")
    return data_dir.joinpath(name)


def tmp_path() -> Path:
    """Return a temporary path."""
    return Path(tempfile.mkdtemp())


def tmp_file() -> Path:
    """Return a temporary file."""
    return Path(tempfile.mkstemp()[1])


def render_diff(diff: difflib.Differ) -> None:
    """Render the diff between the base and repo content.

    Args:
        diff: The diff object.
    """
    for line in diff:
        if line.startswith("---"):
            color = Color.BRIGHT_MAGENTA
        elif line.startswith("+++"):
            color = Color.BRIGHT_CYAN
        elif line.startswith("@@"):
            color = Color.BRIGHT_YELLOW
        elif line.startswith("-"):
            color = Color.BRIGHT_RED
        elif line.startswith("+"):
            color = Color.BRIGHT_GREEN
        else:
            color = Color.GREY
        print(f"{color}{line}{Color.END}")  # noqa: T201


class Spinner:  # pylint: disable=too-many-instance-attributes
    """A spinner."""

    def __init__(
        self: Spinner,
        message: str,
        term_features: TermFeatures,
        delay: float = 0.1,
    ) -> None:
        """Initialize the spinner.

        Args:
            message: The message to display
            term_features: Terminal features
            delay: The delay between characters
        """
        self.spinner = itertools.cycle(("|", "/", "-", "\\", "|", "/", "-"))
        self.delay = delay
        self.busy = False
        self.spinner_visible = False
        self._term_features = term_features
        self._screen_lock = threading.Lock()
        self._start_time: float | None = None
        self.thread: threading.Thread
        self.msg: str = message.rstrip(".").rstrip(":").rstrip()

    def write_next(self: Spinner) -> None:
        """Write the next char."""
        with self._screen_lock:
            if not self.spinner_visible:
                if self._term_features.color:
                    char = f"{Color.GREY}{next(self.spinner)}{Color.END}"
                else:
                    char = next(self.spinner)
                sys.stdout.write(char)
                self.spinner_visible = True
                sys.stdout.flush()

    def remove_spinner(
        self: Spinner,
        cleanup: bool = False,  # noqa: FBT001,FBT002
    ) -> None:
        """Remove the spinner.

        https://github.com/Tagar/stuff/blob/master/spinner.py

        Args:
            cleanup: Should we cleanup after the spinner
        """
        with self._screen_lock:
            if self.spinner_visible:
                sys.stdout.write("\b")
                self.spinner_visible = False
                if cleanup:
                    sys.stdout.write(" ")  # overwrite spinner with blank
                    sys.stdout.write("\r")  # move to next line
                    sys.stdout.write("\033[K")  # clear line
                sys.stdout.flush()

    def spinner_task(self: Spinner) -> None:
        """Spin the spinner."""
        while self.busy:
            self.write_next()
            time.sleep(self.delay)
            self.remove_spinner()

    def __enter__(self: Spinner) -> None:
        """Enter the context handler."""
        # set the start time
        self._start_time = time.time()
        if not self._term_features.any_enabled():
            return
        if self._term_features.color:
            sys.stdout.write(f"{Color.GREY}{self.msg}:{Color.END} ")
        else:
            sys.stdout.write(f"{self.msg}: ")
        # hide the cursor
        sys.stdout.write("\033[?25l")
        if self._term_features.any_enabled():
            self.busy = True
            self.thread = threading.Thread(target=self.spinner_task)
            self.thread.start()

    def __exit__(
        self: Spinner,
        typ: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the context handler.

        Args:
            typ: The exception
            exc: The exception value
            tb: The traceback


        """
        # delay if less than n seconds has elapsed
        if not self._term_features.any_enabled():
            return
        min_show_time = 0.5
        if self._start_time:
            elapsed = time.time() - self._start_time
            if elapsed < min_show_time:
                time.sleep(min_show_time - elapsed)
        if self._term_features.any_enabled():
            self.busy = False
            self.remove_spinner(cleanup=True)
        else:
            sys.stdout.write("\r")
        # show the cursor
        sys.stdout.write("\033[?25h")


def subprocess_run(  # noqa: PLR0913
    command: str,
    verbose: int,
    msg: str,
    output: Output,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command.

    Args:
        command: The command to run
        verbose: The verbosity level
        msg: The message to display
        output: The output object
        cwd: The current working directory
        env: The environment variables
    Returns:
        The completed process
    """
    cmd = f"Running command: {command}"
    output.debug(cmd)
    log_level = logging.ERROR - (verbose * 10)
    if log_level == logging.DEBUG:
        return subprocess_tee.run(
            command,
            check=True,
            cwd=cwd,
            env=env,
            shell=True,  # noqa: S604
            text=True,
        )
    with Spinner(message=msg, term_features=output.term_features):
        return subprocess.run(
            command,
            check=True,
            cwd=cwd,
            env=env,
            shell=True,  # noqa: S602
            capture_output=True,
            text=True,
        )


def ask_yes_no(question: str) -> bool:
    """Ask a question.

    Args:
        question: The question to ask
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(f"{Color.BRIGHT_WHITE}{question} (y/n){Color.END}: ").lower()
    if answer == "y":
        return True
    return False


def get_commit_msg(config: Config, commit_msg: str) -> tuple(str, Path | None):
    """Get the commit message."""
    commit_text_file = tmp_file()
    commit_text_file.write_text(commit_msg)
    initial_ts = commit_text_file.stat().st_mtime
    command = f"{config.editor} {commit_text_file}"
    subprocess.Popen(args=command, shell=True).wait()
    post_ts = commit_text_file.stat().st_mtime
    with commit_text_file.open(mode="r") as f:
        commit_msg = f.read().strip()
    if initial_ts == post_ts:
        return None
    return commit_msg, commit_text_file
