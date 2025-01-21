"""
Extensions to :mod:`click`
"""

import sys
from collections.abc import Callable, Mapping, Sequence
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as tomlLoadFile
from typing import Any, ClassVar, cast
from unittest.mock import patch

import click
from attrs import Factory, mutable
from click import UsageError


__all__ = (
    "ClickTestResult",
    "clickTestRun",
    "readConfig",
)


class Internal(Enum):
    UNSET = auto()


@mutable(kw_only=True)
class ClickTestResult:
    """
    Captured results after testing a click command.
    """

    echoOutputType: ClassVar = list[tuple[str, Mapping[str, Any]]]

    exitCode: int | None | Internal = Internal.UNSET

    echoOutput: echoOutputType = Factory(list)

    stdin: StringIO = Factory(StringIO)
    stdout: StringIO = Factory(StringIO)
    stderr: StringIO = Factory(StringIO)

    beginLoggingToCalls: Sequence[Any] = ()


def clickTestRun(main: Callable[[], None], arguments: list[str]) -> ClickTestResult:
    """
    Context manager for testing click applications.
    """
    assert len(arguments) > 0

    result = ClickTestResult()

    stdin = sys.stdin
    stdout = sys.stdout
    stderr = sys.stderr

    sys.stdin = result.stdin
    sys.stdout = result.stdout
    sys.stderr = result.stderr

    argv = sys.argv
    sys.argv = arguments

    def captureExit(code: int | None = None) -> None:
        # assert result.exitCode == Internal.UNSET, "repeated call to exit()"
        result.exitCode = code

    exit = sys.exit
    sys.exit = cast(Callable, captureExit)

    def captureEcho(format: str, **kwargs: Any) -> None:
        result.echoOutput.append((format, kwargs))

    echo = click.echo
    click.echo = cast(Callable, captureEcho)

    with patch("twisted.logger.globalLogBeginner.beginLoggingTo") as beginLoggingTo:
        main()

    result.beginLoggingToCalls = beginLoggingTo.call_args_list

    sys.stdin = stdin
    sys.stdout = stdout
    sys.stderr = stderr
    sys.argv = argv
    sys.exit = exit
    click.echo = echo

    return result


def readConfig(path: Path) -> dict[str, str | None]:
    """
    Read configuration from the given path.
    """
    path = path.expanduser()

    try:
        try:
            return tomlLoadFile(path.open("rb"))
        except TOMLDecodeError as e:
            raise UsageError(f"Invalid configuration file: {e}") from e
    except FileNotFoundError:
        return {}
