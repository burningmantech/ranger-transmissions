from pathlib import Path
from typing import cast

import click
from attrs import frozen
from click import Context, Group, group, option, pass_context, version_option
from twisted.internet.interfaces import IReactorCore
from twisted.internet.task import react

from transmissions.ext.click import readConfig
from transmissions.ext.logger import startLogging
from transmissions.indexer import Indexer

from ._store import StoreFactory, storeFactoryFromConfig


__all__ = ()


defaultConfigPath = Path("~/rtx.toml")


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
        main(auto_envvar_prefix="RTX")


def groupClassWithConfigParam(param: str) -> type[Group]:
    class GroupWithConfiguration(Group):
        def invoke(self, ctx: Context) -> object:
            if param in ctx.params:
                fileName = ctx.params[param]
                if fileName is not None:
                    if ctx.default_map is None:
                        ctx.default_map = {}
                    if "_config" not in ctx.default_map:
                        config = readConfig(Path(fileName))
                        ctx.default_map["_config"] = config
                        # Set _config on subcommand contexts
                        for command in self.commands:
                            if command not in ctx.default_map:
                                ctx.default_map[command] = {}
                            if "_config" not in ctx.default_map[command]:
                                ctx.default_map[command]["_config"] = config

            return super().invoke(ctx)

    return GroupWithConfiguration


defaultConfigPath = Path("~/.rtx.toml")


@group(cls=groupClassWithConfigParam("config"))
@version_option()
@option(
    "--config",
    help=f"Set path to configuration file. (default: {defaultConfigPath})",
    type=str,
    metavar="<path>",
    prompt=False,
    required=False,
    default=defaultConfigPath,
)
@pass_context
def main(ctx: Context, config: str) -> None:
    """
    Radio transmission indexing tool.
    """
    assert ctx.default_map is not None
    configuration = ctx.default_map["_config"]

    # if ctx.default_map is None:
    #     commonDefaults = readConfig(Path(config))

    #     ctx.default_map = {command: commonDefaults for command in ("index",)}

    configuration["storeFactory"] = storeFactoryFromConfig(configuration)

    startLogging()


def storeFactoryFromContext(ctx: Context) -> StoreFactory:
    """
    Get the data store factory from the given context.
    """
    assert ctx.default_map is not None
    return cast(StoreFactory, ctx.default_map["_config"]["storeFactory"])


@main.command()
def index() -> None:
    """
    Index audio files.
    """
    indexer = Indexer(
        eventID="2023",
        root=(
            Path("~").expanduser()
            / "Google Drive"
            / "Shared drives"
            / "2023 Radio System Archive"
        ),
    )

    for transmission in indexer.transmissions():
        click.echo(f"Transmission: {transmission}")


@main.command()
@pass_context
def events(ctx: Context) -> None:
    """
    List events.
    """
    storeFactory = storeFactoryFromContext(ctx)

    async def run(reactor: IReactorCore) -> None:
        store = await storeFactory()
        for event in await store.events():
            click.echo(str(event))

    react(run)
