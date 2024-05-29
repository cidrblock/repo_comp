"""Parse the command line arguments."""

from __future__ import annotations

import argparse

from argparse import HelpFormatter
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Any

try:
    from ._version import version as __version__  # type: ignore[unused-ignore,import-not-found]
except ImportError:  # pragma: no cover
    try:
        import pkg_resources

        __version__ = pkg_resources.get_distribution(
            "ansible_dev_environment",
        ).version
    except Exception:  # pylint: disable=broad-except # noqa: BLE001
        # this is the fallback SemVer version picked by setuptools_scm when tag
        # information is not available.
        __version__ = "0.1.dev1"


def parse_args() -> argparse.Namespace:
    """Start parsing args passed from Cli.

    Returns:
        The parsed arguments.
    """
    parser = ArgumentParser(
        description="Repository management",
        formatter_class=CustomHelpFormatter,
    )

    parser.add_argument(
        "--na",
        "--no-ansi",
        action="store_true",
        default=False,
        dest="no_ansi",
        help="Disable the use of ANSI codes for terminal color.",
    )

    parser.add_argument(
        "--lf",
        "--log-file <file>",
        dest="log_file",
        default=str(Path.cwd() / "ansible-creator.log"),
        help="Log file to write to.",
    )

    parser.add_argument(
        "--ll",
        "--log-level <level>",
        dest="log_level",
        default="notset",
        choices=["notset", "debug", "info", "warning", "error", "critical"],
        help="Log level for file output.",
    )

    parser.add_argument(
        "--la",
        "--log-append <bool>",
        dest="log_append",
        choices=["true", "false"],
        default="true",
        help="Append to log file.",
    )

    parser.add_argument(
        "-v",
        dest="verbose",
        action="count",
        default=1,
        help="Give more Cli output. Option is additive, and can be used up to 3 times.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print ansible-creator version and exit.",
    )

    parser.add_argument(
        "--cf",
        "--check-forks",
        action="store_true",
        default=False,
        help="Ensure the repo is forked",
    )

    return parser.parse_args()


class ArgumentParser(argparse.ArgumentParser):
    """A custom argument parser."""

    def add_argument(  # type: ignore[override]
        self: ArgumentParser,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Add an argument.

        Args:
            *args: The arguments
            **kwargs: The keyword arguments
        """
        if "choices" in kwargs:
            kwargs["help"] += f" (choices: {', '.join(kwargs['choices'])})"
        if "default" in kwargs and kwargs["default"] != "==SUPPRESS==":
            kwargs["help"] += f" (default: {kwargs['default']})"
        kwargs["help"] = kwargs["help"][0].upper() + kwargs["help"][1:]
        super().add_argument(*args, **kwargs)


class CustomHelpFormatter(HelpFormatter):
    """A custom help formatter."""

    def __init__(self: CustomHelpFormatter, prog: str) -> None:
        """Initialize the help formatter.

        Args:
            prog: The program name
        """
        long_string = "--abc  --really_really_really_log"
        # 3 here accounts for the spaces in the ljust(6) below
        HelpFormatter.__init__(
            self,
            prog=prog,
            indent_increment=1,
            max_help_position=len(long_string) + 3,
        )

    def _format_action_invocation(
        self: CustomHelpFormatter,
        action: argparse.Action,
    ) -> str:
        """Format the action invocation.

        Args:
            action: The action to format

        Raises:
            ValueError: If more than 2 options are given

        Returns:
            The formatted action invocation
        """
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar

        if len(action.option_strings) == 1:
            return action.option_strings[0]

        max_variations = 2
        if len(action.option_strings) == max_variations:
            # Account for a --1234 --long-option-name
            return f"{action.option_strings[0].ljust(6)} {action.option_strings[1]}"
        msg = "Too many option strings"
        raise ValueError(msg)
