from typing import Self

from reflex import Base
from transmissions.model import Transmission


class RXTransmission(Base):
    """
    Reflex model for Transmission
    """

    @classmethod
    def fromTransmission(cls, transmission: Transmission) -> Self:
        if transmission.duration is None:
            duration = None
        else:
            duration = transmission.duration.total_seconds()

        return cls(
            startTime=str(transmission.startTime),
            eventID=transmission.eventID,
            station=transmission.station,
            system=transmission.system,
            channel=transmission.channel,
            duration=duration,
            path=str(transmission.path),
            sha256=transmission.sha256,
            transcription=transmission.transcription,
        )

    startTime: str | None
    eventID: str
    station: str
    system: str
    channel: str
    duration: float | None
    path: str
    sha256: str | None
    transcription: str | None
