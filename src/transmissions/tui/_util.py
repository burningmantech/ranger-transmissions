from datetime import datetime as DateTime

from arrow import get as makeArrow
from rich.markup import escape


__all__ = ()


TransmissionTuple = tuple[
    str, str, str, str, str, str, float | None, str, str | None, str | None
]


def optionalEscape(text: str | None) -> str | None:
    if text is None:
        return None
    else:
        return escape(text)


def dateTimeAsText(datetime: DateTime) -> str:
    return str(makeArrow(datetime))


def dateTimeFromText(text: str) -> DateTime:
    return makeArrow(text).datetime
