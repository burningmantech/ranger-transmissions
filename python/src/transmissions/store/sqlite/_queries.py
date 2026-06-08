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


template_setTransmissionAttribute = """
    update TRANSMISSION set {column} = :value
    where
        EVENT = :eventID and SYSTEM = :system and CHANNEL = :channel and
        START_TIME = :startTime
    """

template_setTransmissionAttribute_fts = """
    update TRANSMISSION_FTS set {column} = :value
    where
        EVENT = :eventID and SYSTEM = :system and CHANNEL = :channel and
        START_TIME = :startTime
    """


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
            FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
        from TRANSMISSION
        """,
    ),
    transmission=Query(
        "look up transmission",
        """
        select
            EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
            FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
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
            FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
        ) values (
            :eventID, :station, :system, :channel, :startTime, :duration,
            :fileName, :sha256, :transcription, :transcriptionVersion
        )
        """,
    ),
    createTransmission_fts=Query(
        "create transmission (FTS)",
        """
        insert into TRANSMISSION_FTS (
            EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
            FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
        ) values (
            :eventID, :station, :system, :channel, :startTime, :duration,
            :fileName, :sha256, :transcription, :transcriptionVersion
        )
        """,
    ),
    setTransmission_duration=Query(
        "set transmission duration",
        template_setTransmissionAttribute.format(column="DURATION"),
    ),
    setTransmission_duration_fts=Query(
        "set transmission duration (FTS)",
        template_setTransmissionAttribute_fts.format(column="DURATION"),
    ),
    setTransmission_sha256=Query(
        "set transmission SHA 256",
        template_setTransmissionAttribute.format(column="SHA256"),
    ),
    setTransmission_sha256_fts=Query(
        "set transmission SHA 256 (FTS)",
        template_setTransmissionAttribute_fts.format(column="SHA256"),
    ),
    setTransmission_transcription=Query(
        "set transmission transcription",
        template_setTransmissionAttribute.format(column="TRANSCRIPTION"),
    ),
    setTransmission_transcription_fts=Query(
        "set transmission transcription (FTS)",
        template_setTransmissionAttribute_fts.format(column="TRANSCRIPTION"),
    ),
    setTransmission_transcriptionVersion=Query(
        "set transmission transcription",
        template_setTransmissionAttribute.format(column="TRANSCRIPTION_VERSION"),
    ),
    setTransmission_transcriptionVersion_fts=Query(
        "set transmission transcription (FTS)",
        template_setTransmissionAttribute_fts.format(column="TRANSCRIPTION_VERSION"),
    ),
)
