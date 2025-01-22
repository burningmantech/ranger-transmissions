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
from attrs.validators import instance_of, optional


__all__ = ()


KeyType = TypeAlias


@frozen(kw_only=True, order=True)
class Transmission:
    """
    Radio transmission
    """

    Key: ClassVar[TypeAlias] = KeyType

    startTime: DateTime = field(validator=instance_of(DateTime))
    eventID: str = field(validator=instance_of(str))
    station: str = field(validator=instance_of(str))
    system: str = field(validator=instance_of(str))
    channel: str = field(validator=instance_of(str))
    duration: TimeDelta | None = field(
        validator=optional(instance_of(TimeDelta)), order=False
    )
    path: Path = field(validator=instance_of(Path))
    sha256: str | None = field(validator=optional(instance_of(str)), order=False)
    transcription: str | None = field(validator=optional(instance_of(str)), order=False)

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
            f"{self.eventID} {self.startTime} ({self.duration})"
            f" [{self.system}: {self.channel}]"
            f" {self.station}: {self.transcription}"
        )
