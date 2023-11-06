from collections.abc import Awaitable, Callable, Iterable
from datetime import datetime as DateTime
from pathlib import Path
from typing import Any, cast

import click
from arrow import get as makeArrow
from attrs import frozen
from click import (
    Context,
    Group,
    UsageError,
    group,
    option,
    pass_context,
    version_option,
)
from rich.box import DOUBLE_EDGE as RICH_DOUBLE_EDGE
from rich.console import Console as RichConsole
from rich.table import Table as RichTable
from twisted.internet import asyncioreactor as asyncioReactor
from twisted.internet import default as defaultReactor
from twisted.internet.interfaces import IReactorCore
from twisted.internet.task import react

from transmissions.ext.click import readConfig
from transmissions.ext.logger import startLogging
from transmissions.indexer import Indexer
from transmissions.model import Event, Transmission
from transmissions.store import TXDataStore

from ._application import TransmissionsApp
from ._store import StoreFactory, storeFactoryFromConfig


__all__ = ()


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


def configuredEventsFromContext(ctx: Context) -> Iterable[tuple[Event, Path]]:
    """
    Get events from the given context.
    """
    assert ctx.default_map is not None

    eventConfig = ctx.default_map["_config"].get("Audio", {}).get("Event", {})

    for eventID, eventDict in eventConfig.items():
        try:
            eventName = eventDict["Name"]
        except KeyError as e:
            raise UsageError(f"No name specified for event {eventID}") from e

        event = Event(id=eventID, name=eventName)

        try:
            sourcePath = Path(eventDict["SourceDirectory"]).expanduser()
        except KeyError as e:
            raise UsageError(
                f"No source directory specified for event {eventID}"
            ) from e

        if not sourcePath.is_dir():
            raise UsageError(
                f"No source directory found for event {eventID}: {sourcePath}"
            )

        yield (event, sourcePath)


Application = Callable[[TXDataStore], Awaitable[None]]


def run(
    ctx: Context, app: Application, *, reactor: Any = defaultReactor
) -> None:
    """
    Interact with the data.
    """
    reactor.install()

    storeFactory = storeFactoryFromContext(ctx)

    async def runInReactor(reactor: IReactorCore) -> None:
        try:
            store = await storeFactory()
            try:
                await app(store)
            finally:
                await store.close()
        except KeyboardInterrupt:
            click.echo("Interrupted.")

    react(runInReactor)


def printEvents(events: Iterable[Event]) -> None:
    console = RichConsole()

    table = RichTable(show_header=True, box=RICH_DOUBLE_EDGE)
    table.add_column("ID")
    table.add_column("NAME")

    for event in events:
        table.add_row(event.id, event.name)

    console.print(table)


def printTransmissions(transmissions: Iterable[Transmission]) -> None:
    console = RichConsole()

    table = RichTable(show_header=True, box=RICH_DOUBLE_EDGE)
    table.add_column("Event")
    table.add_column("Station")
    table.add_column("System")
    table.add_column("Channel")
    table.add_column("Start")
    table.add_column("Duration")
    table.add_column("Text")

    unknown = "-?-"

    def displayDateTime(dateTime: DateTime) -> str:
        arrow = makeArrow(dateTime).to("US/Pacific")
        return arrow.format("MM/DD HH:mm:ss")

    for transmission in transmissions:
        if transmission.duration is None:
            duration = unknown
        else:
            duration = str(transmission.duration)

        if transmission.transcription is None:
            transcription = unknown
        else:
            transcription = transmission.transcription

        table.add_row(
            transmission.eventID,
            transmission.station,
            transmission.system,
            transmission.channel,
            displayDateTime(transmission.startTime),
            duration,
            transcription,
        )

    console.print(table)


@main.command()
@pass_context
def index(ctx: Context) -> None:
    """
    Index audio files.
    """
    configuredEvents = configuredEventsFromContext(ctx)

    async def app(store: TXDataStore) -> None:
        for event, sourcePath in configuredEvents:
            indexer = Indexer(event=event, root=sourcePath)
            await indexer.indexIntoStore(store)

    run(ctx, app)


@main.command()
@pass_context
def events(ctx: Context) -> None:
    """
    List events.
    """

    async def app(store: TXDataStore) -> None:
        printEvents(await store.events())

    run(ctx, app)


@main.command()
@pass_context
def transmissions(ctx: Context) -> None:
    """
    List transmissions.
    """

    async def app(store: TXDataStore) -> None:
        printTransmissions(await store.transmissions())

    run(ctx, app)


@main.command()
@pass_context
def application(ctx: Context) -> None:
    """
    Interactive UI.
    """

    async def app(store: TXDataStore) -> None:
        app = TransmissionsApp(await store.transmissions())
        app.run()

    run(ctx, app, reactor=asyncioReactor)
