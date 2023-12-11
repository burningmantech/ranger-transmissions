from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from enum import Enum, unique
from typing import Any, cast

from .._transmission import Transmission
from ._json import (
    deserialize,
    jsonSerialize,
    registerDeserializer,
    registerSerializer,
)


__all__ = ()


@unique
class TransmissionJSONKey(Enum):
    """
    Transmission JSON keys
    """

    startTime = "start_time"
    eventID = "event_id"
    station = "station"
    system = "system"
    channel = "channel"
    duration = "duration"
    sha256 = "sha265"
    transcription = "transcription"


class TransmissionJSONType(Enum):
    """
    Transmission attribute types
    """

    startTime = DateTime
    eventID = str
    station = str
    system = str
    channel = str
    duration = TimeDelta
    sha256 = str
    transcription = str


def serializeTransmission(transmission: Transmission) -> dict[str, Any]:
    # Map transmission attribute names to JSON dict key names
    return {
        key.value: jsonSerialize(getattr(transmission, key.name))
        for key in TransmissionJSONKey
    }


registerSerializer(Transmission, serializeTransmission)


def deserializeTransmission(
    obj: dict[str, Any], cl: type[Transmission]
) -> Transmission:
    assert cl is Transmission, (cl, obj)

    return cast(
        Transmission,
        deserialize(
            obj,
            Transmission,
            TransmissionJSONType,
            TransmissionJSONKey,
        ),
    )


registerDeserializer(Transmission, deserializeTransmission)
