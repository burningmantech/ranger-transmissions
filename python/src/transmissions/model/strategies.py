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
Test strategies for model data.
"""

from collections.abc import Callable
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from typing import Any

from hypothesis.strategies import SearchStrategy, composite, integers, text
from hypothesis.strategies import datetimes as _datetimes

from ._event import Event


__all__ = (
    "dateTimes",
    "events",
)


##
# DateTimes
##


@composite
def timeZones(draw: Callable[..., Any]) -> TimeZone:
    """
    Strategy that generates :class:`TimeZone` values.
    """
    offset = draw(integers(min_value=-(60 * 24) + 1, max_value=(60 * 24) - 1))
    timeDelta = TimeDelta(minutes=offset)
    return TimeZone(offset=timeDelta, name=f"{offset}s")


def dateTimes(
    beforeNow: bool = False, fromNow: bool = False
) -> SearchStrategy:  # DateTime
    """
    Strategy that generates :class:`DateTime` values.
    """
    assert not (beforeNow and fromNow)

    #
    # min_value >= UTC epoch because otherwise we can't store dates as UTC
    # timestamps.
    #
    # We actually add a day of fuzz below because min_value doesn't allow
    # non-naive values (?!) so that ensures we have a value after the epoch
    #
    # For all current uses of model date-times in model objects in this module,
    # limiting values to those past the is totally OK.
    #
    fuzz = TimeDelta(days=1)

    if beforeNow:
        max = DateTime.now() - fuzz
    else:
        max = DateTime(9999, 12, 31, 23, 59, 59, 999999)

    if fromNow:
        min = DateTime.now() + fuzz
    else:
        min = DateTime(1970, 1, 1) + fuzz

    return _datetimes(min_value=min, max_value=max, timezones=timeZones())


##
# Event
##


@composite
def events(draw: Callable[..., Any]) -> Event:
    """
    Strategy that generates :class:`Event` values.
    """
    return Event(id=draw(text(min_size=1)), name=draw(text(min_size=1)))
