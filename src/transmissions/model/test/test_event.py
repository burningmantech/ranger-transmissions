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
Tests for transmissions.model._event
"""

from hypothesis import given
from twisted.trial.unittest import SynchronousTestCase as TestCase

from .._event import Event
from ..strategies import events


__all__ = ()


class EventTests(TestCase):
    """
    Tests for :class:`Event`
    """

    @given(events())
    def test_str(self, event: Event) -> None:
        """
        :meth:`Event.__str__` renders the event as a string.
        """
        self.assertEqual(str(event), f"{event.id}: {event.name}")
