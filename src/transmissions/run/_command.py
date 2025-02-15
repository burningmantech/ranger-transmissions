from collections.abc import Awaitable, Callable, Iterable
from csv import writer as csvWriter
from datetime import datetime as DateTime
from pathlib import Path
from sys import stdout
from typing import Any, cast

import click
from arrow import get as makeArrow
from attrs import frozen
from click import Choice as ClickChoice
from click import (
    Context,
    Group,
    UsageError,
    group,
    option,
    pass_context,
    version_option,
)
from click import DateTime as ClickDateTime
from click import Path as ClickPath
from rich.box import DOUBLE_EDGE as RICH_DOUBLE_EDGE
from rich.console import Console as RichConsole
from rich.table import Table as RichTable
from twisted.application.runner._runner import Runner
from twisted.internet import asyncioreactor as asyncioReactor
from twisted.internet import default as defaultReactor
from twisted.internet.defer import Deferred, ensureDeferred
from twisted.internet.interfaces import IReactorCore, IReactorTCP
from twisted.internet.task import react
from twisted.logger import Logger
from twisted.web.server import Site

from transmissions.ext.click import readConfig
from transmissions.ext.logger import startLogging
from transmissions.indexer import Indexer
from transmissions.model import Event, Transmission, TZInfo
from transmissions.store import TXDataStore
from transmissions.tui import Application as TUIApplication

from ._search import SearchIndexFactory, searchIndexFactoryFromConfig
from ._store import StoreFactory, storeFactoryFromConfig


__all__ = ()


log = Logger()

dateTimeFormats = (
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
)


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


def configurationFromContext(ctx: Context) -> dict[str, Any]:
    """
    Get the configuration from the given context.
    """
    assert ctx.default_map is not None
    assert "_config" in ctx.default_map
    return cast(dict[str, Any], ctx.default_map["_config"])


def storeFactoryFromContext(ctx: Context) -> StoreFactory:
    """
    Get the data store factory from the given context.
    """
    configuration = configurationFromContext(ctx)
    return cast(StoreFactory, configuration["storeFactory"])


def searchIndexFactoryFromContext(ctx: Context) -> SearchIndexFactory:
    """
    Get the search index factory from the given context.
    """
    configuration = configurationFromContext(ctx)
    return cast(SearchIndexFactory, configuration["searchIndexFactory"])


def configuredEventsFromContext(ctx: Context) -> Iterable[tuple[Event, Path]]:
    """
    Get events from the given context.
    """
    configuration = configurationFromContext(ctx)
    eventConfig = configuration.get("Audio", {}).get("Event", {})

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
    ctx: Context,
    app: Application,
    *,
    reactor: IReactorTCP = cast(IReactorTCP, defaultReactor),
) -> None:
    """
    Interact with the data.
    """
    reactor.install()  # type: ignore[attr-defined]

    storeFactory = storeFactoryFromContext(ctx)

    async def runInReactor(reactor: IReactorTCP) -> None:  # noqa: ARG001
        try:
            store = await storeFactory()
            try:
                await app(store)
            finally:
                await store.close()
        except KeyboardInterrupt:
            click.echo("Interrupted.")

    startLogging()
    react(runInReactor)


def printEvents(events: Iterable[Event]) -> None:
    console = RichConsole()

    table = RichTable(show_header=True, box=RICH_DOUBLE_EDGE)
    table.add_column("ID")
    table.add_column("NAME")

    for event in events:
        table.add_row(event.id, event.name)

    console.print(table)


def printTransmissionsRich(transmissions: Iterable[Transmission]) -> None:
    console = RichConsole()

    table = RichTable(show_header=True, box=RICH_DOUBLE_EDGE)
    table.add_column("Event")
    table.add_column("Station")
    table.add_column("System")
    table.add_column("Channel")
    table.add_column("Start")
    table.add_column("Duration")
    table.add_column("Transcription")

    unknown = "…"

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


def printTransmissionsCSV(transmissions: Iterable[Transmission]) -> None:
    writer = csvWriter(stdout)
    writer.writerow(
        (
            "Event",
            "Station",
            "System",
            "Channel",
            "Start",
            "Duration",
            "Transcription",
        )
    )
    for transmission in transmissions:
        writer.writerow(
            (
                transmission.eventID,
                transmission.station,
                transmission.system,
                transmission.channel,
                transmission.startTime,
                transmission.duration,
                transmission.transcription,
            )
        )


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
def main(ctx: Context, config: str) -> None:  # noqa: ARG001
    """
    Radio transmission indexing tool.
    """
    configuration = configurationFromContext(ctx)
    configuration["storeFactory"] = storeFactoryFromConfig(configuration)
    configuration["searchIndexFactory"] = searchIndexFactoryFromConfig(configuration)


@main.command()
@option("--new/--no-new", default=True, help="Search for new transmissions")
@option("--checksum/--no-checksum", default=True, help="Compute checksums")
@option("--duration/--no-duration", default=True, help="Compute durations")
@option("--transcript/--no-transcript", default=True, help="Compute transcripts")
@pass_context
def index(
    ctx: Context, new: bool, checksum: bool, duration: bool, transcript: bool
) -> None:
    """
    Index audio files.
    """
    configuredEvents = configuredEventsFromContext(ctx)

    async def app(store: TXDataStore) -> None:
        for event, sourcePath in configuredEvents:
            indexer = Indexer(event=event, root=sourcePath)
            await indexer.indexIntoStore(
                store,
                existingOnly=not new,
                computeChecksum=checksum,
                computeDuration=duration,
                computeTranscription=transcript,
            )

    run(ctx, app)


@main.command()
@click.argument(
    "file",
    type=ClickPath(path_type=Path),
    nargs=-1,
)
@pass_context
def inspect(ctx: Context, file: tuple[Path]) -> None:
    """
    Inspect a transmission file and show information about it.
    """
    configuredEvents = configuredEventsFromContext(ctx)

    async def app(_store: TXDataStore) -> None:
        for _filePath in file:
            filePath = _filePath.resolve()

            for event, _sourcePath in configuredEvents:
                sourcePath = _sourcePath.resolve()

                # If filePath isn't in sourcePath, it isn't in event
                if filePath.parts[: len(sourcePath.parts)] != sourcePath.parts:
                    continue

                indexer = Indexer(event=event, root=sourcePath)
                transmission = indexer.transmissionFromFile(filePath)

                click.echo(str(transmission))

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
@option(
    "--search",
    help="Filter output with the given search query.",
    type=str,
    metavar="<query>",
    prompt=False,
    required=False,
    default="",
)
@option(
    "--start",
    help="Filter output to transmissions starting after the given time.",
    type=ClickDateTime(formats=(dateTimeFormats)),
    metavar="<YYYY-MM-DDTHH:MM>",
    prompt=False,
    required=False,
    default=None,
)
@option(
    "--end",
    help="Filter output to transmissions ending before the given time.",
    type=ClickDateTime(formats=(dateTimeFormats)),
    metavar="<YYYY-MM-DDTHH:MM>",
    prompt=False,
    required=False,
    default=None,
)
@option(
    "--format",
    help="Output format.",
    type=ClickChoice(["text", "csv"]),
    prompt=False,
    required=False,
    default="text",
)
@pass_context
def transmissions(
    ctx: Context, search: str, start: DateTime | None, end: DateTime | None, format: str
) -> None:
    """
    List transmissions.
    """

    if start is not None:
        start = start.replace(tzinfo=TZInfo.PDT.value)
    if end is not None:
        end = end.replace(tzinfo=TZInfo.PDT.value)

    async def app(store: TXDataStore) -> None:
        transmissionsByKey = {t.key: t for t in await store.transmissions()}

        if search:
            searchIndex = await searchIndexFactoryFromContext(ctx)(store)
            transmissions: Iterable[Transmission] = sorted(
                [
                    transmissionsByKey[key]
                    async for key in searchIndex.search(search)
                    if transmissionsByKey[key].isInRange(start, end)
                ]
            )
        else:
            transmissions = sorted(
                tx for tx in transmissionsByKey.values() if tx.isInRange(start, end)
            )

        if format == "text":
            printTransmissionsRich(transmissions)
        elif format == "csv":
            printTransmissionsCSV(transmissions)
        else:
            raise AssertionError(f"Unknown format: {format}")

    run(ctx, app)


@main.command()
@pass_context
def application(ctx: Context) -> None:
    """
    Interactive UI.
    """

    async def app(store: TXDataStore) -> None:
        searchIndex = await searchIndexFactoryFromContext(ctx)(store)
        app = TUIApplication(await store.transmissions(), searchIndex)
        app.run()

    run(ctx, app, reactor=cast(IReactorTCP, asyncioReactor))


@main.command()
@pass_context
def web(ctx: Context) -> None:
    """
    Web server.
    """
    from twisted.internet import reactor

    from transmissions.webapi import Application as WebAPIApplication

    configuration = configurationFromContext(ctx)
    storeFactory = storeFactoryFromContext(ctx)

    def whenRunning() -> Deferred[None]:
        async def run() -> None:
            store = await storeFactory()

            host = "localhost"
            port = 8080

            log.info(
                "Setting up web service at http://{host}:{port}/",
                host=host,
                port=port,
            )

            application = WebAPIApplication(config=configuration, store=store)
            factory = Site(application.router.resource())
            cast(IReactorTCP, reactor).listenTCP(port, factory, interface=host)

        return ensureDeferred(run())

    runner = Runner(
        reactor=cast(IReactorCore, reactor),
        # defaultLogLevel=X,
        # logFile=stdout,
        # fileLogObserverFactory=fileLogObserverFactory,
        whenRunning=whenRunning,  # type: ignore[arg-type]
        # whenRunningArguments={},
    )
    runner.run()
