from typing import ClassVar, Self, overload

from reflex import Base

from transmissions.model import Transmission, TZInfo


class RXTransmission(Base):
    """
    Reflex model for Transmission
    """

    dateTimeFormat: ClassVar[str] = "%y-%m-%d %H:%M:%S%z"

    @overload
    @classmethod
    def fromTransmission(cls, transmission: Transmission) -> Self: ...

    @overload
    @classmethod
    def fromTransmission(cls, transmission: None) -> None: ...

    @classmethod
    def fromTransmission(cls, transmission: Transmission | None) -> Self | None:
        if transmission is None:
            return None
        return cls(
            startTime=transmission.startTime.astimezone(TZInfo.PDT.value).strftime(
                cls.dateTimeFormat
            ),
            eventID=transmission.eventID,
            station=transmission.station,
            system=transmission.system,
            channel=transmission.channel,
            duration=(
                transmission.duration.total_seconds() if transmission.duration else None
            ),
            transcription=transmission.transcription,
        )

    startTime: str
    eventID: str
    station: str
    system: str
    channel: str
    duration: float | None
    transcription: str | None
