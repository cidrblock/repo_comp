"""The configuration module for the repo_comp package."""

from __future__ import annotations

import datetime

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from repo_comp.output import Output
    from repo_comp.repo import Repo


@dataclass
class Config:
    """The configuration data for the repo_comp package."""

    args: Namespace
    editor: str
    output: Output
    repos: list[Repo] = None
    tmp_path: Path = None
    session_id: str = ""

    def __post_init__(self: Config) -> None:
        """Post initialization."""
        self.session_id = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%y%m%d-%H%M%S",
        )
