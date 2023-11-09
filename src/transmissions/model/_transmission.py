# -*- test-case-name: mixer.model.test.test_transmission -*-

##
# See the file COPYRIGHT for copyright information.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

"""
Radio transmission
"""

from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from pathlib import Path
from typing import ClassVar, TypeAlias

from attrs import field, frozen


__all__ = ()


KeyType = TypeAlias


@frozen(kw_only=True, order=True)
class Transmission:
    """
    Radio transmission
    """

    Key: ClassVar[TypeAlias] = KeyType

    startTime: DateTime = field()
    eventID: str = field()
    station: str = field()
    system: str = field()
    channel: str = field()
    duration: TimeDelta | None = field(order=False)
    path: Path = field()
    sha256: str | None = field(order=False)
    transcription: str | None = field(order=False)

    @startTime.validator
    def _check_startTime(self, attribute: object, value: object) -> None:
        if not isinstance(value, DateTime):
            raise TypeError("startTime must be a DateTime")

    @eventID.validator
    def _check_eventID(self, attribute: object, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError("eventID must be a str")

    @station.validator
    def _check_station(self, attribute: object, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError("station must be a str")

    @system.validator
    def _check_system(self, attribute: object, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError("system must be a str")

    @channel.validator
    def _check_channel(self, attribute: object, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError("channel must be a str")

    @duration.validator
    def _check_duration(self, attribute: object, value: object) -> None:
        if value is not None and not isinstance(value, TimeDelta):
            raise TypeError("duration must be a TimeDelta or None")

    @path.validator
    def _check_path(self, attribute: object, value: object) -> None:
        if not isinstance(value, Path):
            raise TypeError("path must be a Path")

    @sha256.validator
    def _check_sha256(self, attribute: object, value: object) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("sha256 must be a str or None")

    @transcription.validator
    def _check_transcription(self, attribute: object, value: object) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("transcription must be a str or None")

    @property
    def endTime(self) -> DateTime | None:
        if self.duration is None:
            return None
        return self.startTime + self.duration

    @property
    def key(self) -> Key:
        return (self.eventID, self.system, self.channel, self.startTime)

    def __str__(self) -> str:
        return (
            f"{self.startTime} ({self.duration})"
            f" [{self.system}: {self.channel}]"
            f" {self.station}: {self.transcription}"
        )
