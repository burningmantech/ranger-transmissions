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
Transmissions SQLite queries.
"""

from .._db import Queries, Query


__all__ = ()


queries = Queries(
    schemaVersion=Query(
        "look up schema version",
        """
        select VERSION from SCHEMA_INFO
        """,
    ),
    events=Query(
        "look up events",
        """
        select ID, NAME from EVENT
        """,
    ),
    createEvent=Query(
        "create event",
        """
        insert into EVENT (ID, NAME) values (:eventID, :eventName)
        """,
    ),
    createEventOrIgnore=Query(
        "create event if no matching event already exists",
        """
        insert or ignore into EVENT (ID, NAME) values (:eventID, :eventName)
        """,
    ),
    transmissions=Query(
        "look up transmissions",
        """
        select
            EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
            FILE_NAME, SHA256, TRANSCRIPTION
        from TRANSMISSION
        """,
    ),
    transmission=Query(
        "look up transmission",
        """
        select
            EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
            FILE_NAME, SHA256, TRANSCRIPTION
        from TRANSMISSION
        where
            EVENT = :eventID and SYSTEM = :system and CHANNEL = :channel and
            START_TIME = :startTime
        """,
    ),
    createTransmission=Query(
        "create transmission",
        """
        insert into TRANSMISSION (
            EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
            FILE_NAME, SHA256, TRANSCRIPTION
        ) values (
            :eventID, :station, :system, :channel, :startTime, :duration,
            :fileName, :sha256, :transcription
        )
        """,
    ),
)
