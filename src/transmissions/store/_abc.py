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
Transmissions data store abstract base classes.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime as DateTime

from transmissions.model import Event, Transmission


__all__ = ()


class TXDataStore(ABC):
    """
    Transmissions data store abstract base class.
    """

    ##
    # Database management
    ##

    @abstractmethod
    async def upgradeSchema(self) -> None:
        """
        Upgrade the data store schema to the current version.
        """

    @abstractmethod
    async def validate(self) -> None:
        """
        Perform some data integrity checks and raise :exc:`StorageError` if
        there are any problems detected.
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close any existing connections, close files, etc.
        """

    ###
    # Events
    ###

    @abstractmethod
    async def events(self) -> Iterable[Event]:
        """
        Look up all events in this store.
        """

    @abstractmethod
    async def createEvent(self, event: Event) -> None:
        """
        Create the given event.
        """

    ###
    # Transmissions
    ###

    @abstractmethod
    async def transmissions(self) -> Iterable[Transmission]:
        """
        Look up all transmissions in this store.
        """

    @abstractmethod
    async def transmission(
        self, eventID: str, system: str, channel: str, startTime: DateTime
    ) -> Transmission | None:
        """
        Look up the transmission in this store with the given event, system,
        channel, and start time.
        """

    @abstractmethod
    async def createTransmission(self, transmission: Transmission) -> None:
        """
        Create the given transmission.
        """
