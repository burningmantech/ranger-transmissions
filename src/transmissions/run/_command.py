from pathlib import Path

from attrs import frozen
from click import Context as ClickContext
from click import group as commandGroup
from click import option as commandOption
from click import pass_context as passContext
from click import version_option as versionOption

from transmissions.ext.click import defaultConfigPath, readConfig
from transmissions.ext.logger import startLogging


@frozen(kw_only=True)
class Command:
    """
    Radio Transmission Command Line Tool
    """

    @classmethod
    def main(cls) -> None:
        """
        Command line entry point.
        """
        main()


@commandGroup()
@versionOption()
@commandOption(
    "--config",
    help=f"Set path to configuration file. (default: {defaultConfigPath})",
    type=str,
    metavar="<path>",
    prompt=False,
    required=False,
)
@passContext
def main(ctx: ClickContext, config: str = defaultConfigPath) -> None:
    """
    Radio transmission indexing tool.
    """
    if ctx.default_map is None:
        commonDefaults = readConfig(Path(config))

        ctx.default_map = {command: commonDefaults for command in ("index",)}

    startLogging()


@main.command()
def index() -> None:
    """
    Index audio files.
    """
