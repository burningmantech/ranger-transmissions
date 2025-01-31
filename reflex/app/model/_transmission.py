from typing import Self

from reflex import Base
from transmissions.model import Transmission


class RXTransmission(Base):
    """
    Reflex model for Transmission
    """

    @classmethod
    def fromTransmission(cls, transmission: Transmission) -> Self:
        if transmission is None:
            return None
        return cls(
            startTime=transmission.startTime.isoformat(),
            eventID=transmission.eventID,
            station=transmission.station,
            system=transmission.system,
            channel=transmission.channel,
            duration=(
                transmission.duration.total_seconds() if transmission.duration else None
            ),
            sha256=transmission.sha256,
            transcription=transmission.transcription,
        )

    startTime: str
    eventID: str
    station: str
    system: str
    channel: str
    duration: float | None
    sha256: str | None
    transcription: str | None
