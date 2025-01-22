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
Incident Management System data model JSON serialization/deserialization
"""

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from enum import Enum
from json import JSONEncoder, dumps, loads
from typing import Any, ClassVar, cast

from arrow.parser import DateTimeParser
from cattr import Converter
from twisted.logger import Logger


__all__ = ()


log = Logger()


JSON = Mapping[str, Any] | Iterable[Any] | int | str | float | bool | None


class Encoder(JSONEncoder):
    """
    JSON encoder that attempts to convert :class:`Mapping` to :class:`dict`,
    and other types of :class:`Iterable` to :class:`list`.
    """

    _log: ClassVar[Logger] = Logger()

    def default(self, obj: Any) -> Any:
        iterate = getattr(obj, "__iter__", None)
        if iterate is not None:
            # We have an Iterable
            if hasattr(obj, "__getitem__"):
                # We have a Mapping
                return dict(obj)
            return list(iterate())

        with self._log.failuresHandled(
            "Unable to encode object {obj!r}:", obj=obj
        ) as op:
            result = JSONEncoder.default(self, obj)
        if op.failure is not None:
            op.failure.raiseException()
        return result


class JSONCodecError(Exception):
    """
    Error while serializing or deserializing JSON data.
    """


def jsonTextFromObject(obj: JSON, pretty: bool = False) -> str:
    """
    Convert an object into JSON text.

    :param obj: An object that is serializable to JSON.

    :param pretty: Whether to format for easier human consumption.
    """
    if pretty:
        separators = (",", ": ")
        indent: int | None = 2
        sortKeys = True
    else:
        separators = (",", ":")
        indent = None
        sortKeys = False

    return dumps(
        obj,
        ensure_ascii=False,
        separators=separators,
        indent=indent,
        sort_keys=sortKeys,
        cls=Encoder,
    )


def objectFromJSONText(text: str) -> Any:
    """
    Convert JSON text into an object.
    """
    return loads(text)


converter = Converter()

jsonSerialize: Callable[[Any], JSON] = converter.unstructure
jsonDeserialize = converter.structure

registerSerializer = converter.register_unstructure_hook
registerDeserializer = converter.register_structure_hook


# DateTime


def dateTimeAsISOText(dateTime: DateTime) -> str:
    return dateTime.isoformat()


def isoTextAsDateTime(isoText: str) -> DateTime:
    return DateTimeParser().parse_iso(isoText)


def deserializeDateTime(obj: str, cl: type[DateTime]) -> DateTime:
    assert cl is DateTime, (cl, obj)
    return isoTextAsDateTime(obj)


registerSerializer(DateTime, dateTimeAsISOText)
registerDeserializer(DateTime, deserializeDateTime)


def timeDeltaAsSeconds(timedelta: TimeDelta) -> int:
    return timedelta.seconds


def secondsAsTimeDelta(seconds: int) -> TimeDelta:
    return TimeDelta(seconds=seconds)


def deserializeTimeDelta(obj: int, cl: type[TimeDelta]) -> TimeDelta:
    assert cl is TimeDelta, (cl, obj)
    return secondsAsTimeDelta(obj)


registerSerializer(TimeDelta, timeDeltaAsSeconds)
registerDeserializer(TimeDelta, deserializeTimeDelta)


# Tuples and sets should serialize like lists


def serializeIterable(iterable: Iterable[Any]) -> list[JSON]:
    return [jsonSerialize(item) for item in iterable]


registerSerializer(frozenset, serializeIterable)
registerSerializer(set, serializeIterable)
registerSerializer(tuple, serializeIterable)


# Public API


def jsonObjectFromModelObject(model: Any) -> JSON:
    return jsonSerialize(model)


def modelObjectFromJSONObject(json: JSON, modelClass: type) -> Any:
    try:
        return jsonDeserialize(json, modelClass)
    except KeyError as e:
        raise JSONCodecError(f"Invalid JSON for {modelClass.__name__}: {json}") from e


# Utilities


def deserialize(
    obj: dict[str, Any],
    cls: type[Any],
    typeEnum: type[Enum],
    keyEnum: type[Enum],
) -> Any:
    def deserializeKey(key: Enum) -> Any:
        try:
            cls = getattr(typeEnum, key.name).value
        except AttributeError as e:
            raise AttributeError(
                f"No attribute {key.name!r} in type enum {typeEnum!r}"
            ) from e
        with log.failuresHandled(
            "Unable to deserialize {key} as {cls} from {json}",
            key=key,
            cls=cls,
            json=obj,
        ) as op:
            result = jsonDeserialize(obj.get(key.value, None), cls)
        if op.failure is not None:
            op.failure.raiseException()
        return result

    return cls(
        **{key.name: deserializeKey(key) for key in cast(Iterable[Enum], keyEnum)}
    )
