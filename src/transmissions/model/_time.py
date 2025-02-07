from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from enum import Enum


class TZInfo(Enum):
    """
    Time zones
    """

    PDT = TimeZone(TimeDelta(hours=-7), name="Pacific Daylight Time")
