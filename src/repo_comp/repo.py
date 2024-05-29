"""A data structure for a repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Repo:
    """A data structure for a repository."""

    origin: str
    upstream: str
    name: str

    origin_uri: str = ""
    upstream_uti: str = ""
    work_dir: Path = None
    origin_owner: str = ""

    def __post_init__(self: Repo) -> None:
        """Post initialization."""
        self.origin_uri = f"git@github.com:{self.origin}.git"
        self.upstream_uri = f"git@github.com{self.upstream}.git"
        self.origin_owner = self.origin.split("/")[0]
