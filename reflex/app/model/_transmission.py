from pathlib import Path
from typing import Self

from reflex import Base
from transmissions.model import Transmission


class RXTransmission(Base):
    """
    Reflex model for Transmission
    """

    @classmethod
    def fromTransmission(cls, transmission: Transmission) -> Self:
        return cls(
            startTime=transmission.startTime.strftime("%Y-%m-%d %H:%M:%S"),
            eventID=transmission.eventID,
            station=transmission.station,
            system=transmission.system,
            channel=transmission.channel,
            duration=(
                transmission.duration.total_seconds() if transmission.duration else None
            ),
            path=transmission.path,
            sha256=transmission.sha256,
            transcription=transmission.transcription,
        )

    startTime: str
    eventID: str
    station: str
    system: str
    channel: str
    duration: float | None
    path: Path
    sha256: str | None
    transcription: str | None
