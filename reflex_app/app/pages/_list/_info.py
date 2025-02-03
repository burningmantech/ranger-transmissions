"""
Transmission Info
"""

from reflex import (
    Component,
    audio,
    blockquote,
    card,
    code,
    cond,
    divider,
    heading,
    text,
    vstack,
)

from ._state import State


def selectedTransmissionInfo() -> Component:
    """
    Information about the selected transmission.
    """
    transmission = State.selectedTransmission

    return cond(
        transmission,
        card(
            vstack(
                heading("Selected Transmission", as_="h2"),
                divider(),
                text(
                    "Station ",
                    code(transmission.station),
                    " on channel ",
                    code(transmission.channel),
                    " at ",
                    text.strong(transmission.startTime),
                ),
                divider(),
                text("Transcript:"),
                blockquote(transmission.transcription),
                divider(),
                audio(
                    url=State.selectedTransmissionAudioURL,
                    width="100%",
                    height="32px",
                ),
                width="100%",
            ),
            width="100%",
        ),
        card(
            vstack(
                text("No transmission selected"),
                width="100%",
            ),
            width="100%",
        ),
    )
