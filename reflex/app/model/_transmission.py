from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
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
            startTime=transmission.startTime,
            eventID=transmission.eventID,
            station=transmission.station,
            system=transmission.system,
            channel=transmission.channel,
            duration=transmission.duration,
            path=transmission.path,
            sha256=transmission.sha256,
            transcription=transmission.transcription,
        )

    startTime: DateTime | None
    eventID: str
    station: str
    system: str
    channel: str
    duration: TimeDelta | None
    path: Path
    sha256: str | None
    transcription: str | None
