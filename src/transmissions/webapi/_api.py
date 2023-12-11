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
Transmissions JSON API web application.
"""

from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import Any, ClassVar

from attrs import frozen
from klein import Klein
from twisted.logger import Logger
from twisted.web.iweb import IRequest

from transmissions.model import Transmission
from transmissions.model.json import (
    jsonObjectFromModelObject,
    jsonTextFromObject,
)
from transmissions.store import TXDataStore


__all__ = ()


class ContentType(StrEnum):
    """
    MIME content types.
    """

    json = "application/json"
    text = "text/plain"


class HeaderName(StrEnum):
    """
    HTTP header names.
    """

    contentType = "Content-Type"


def writeJSONArray(
    request: IRequest, items: Iterable[Any], asJSONBytes: Callable[[Any], bytes]
) -> None:
    first = True
    request.write(b"[")
    for item in items:
        if first:
            first = False
        else:
            request.write(b",")
        request.write(asJSONBytes(item))
    request.write(b"]")


@frozen(kw_only=True, eq=False)
class Application:
    """
    Transmissions JSON API web application.
    """

    log: ClassVar[Logger] = Logger()
    router: ClassVar[Klein] = Klein()

    config: dict[str, Any]
    store: TXDataStore

    @router.route("/")
    async def rootEndpoint(self, request: IRequest) -> str:
        request.setHeader(HeaderName.contentType, ContentType.text)

        return "transmissions API server"

    @router.route("/transmissions/")
    async def transmissionsEndpoint(self, request: IRequest) -> bytes:
        """
        Transmissions endpoint.
        """
        transmissions = await self.store.transmissions()

        def asJSONBytes(transmission: Transmission) -> bytes:
            return jsonTextFromObject(
                jsonObjectFromModelObject(transmission)
            ).encode("utf-8")

        request.setHeader(HeaderName.contentType, ContentType.json)
        writeJSONArray(request, transmissions, asJSONBytes)
        return b""
