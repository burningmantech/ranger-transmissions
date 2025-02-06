"""
Transmissions filters
"""

from reflex import Component, form, hstack, input, select, vstack

from ._state import State


def transmissionsFilters() -> Component:
    """
    Transmissions filters
    """
    return (
        form(
            vstack(
                hstack(
                    select(
                        State.events,
                        value=State.selectedEvent,
                        on_change=State.eventSelected,
                        label="Event",
                    ),
                    input(
                        type="datetime-local",
                        name="start_time",
                        placeholder="Start Time",
                        value=State.startTime,
                        on_change=State.startTimeEdited,
                    ),
                    input(
                        type="datetime-local",
                        name="end_time",
                        value=State.endTime,
                        on_change=State.endTimeEdited,
                    ),
                ),
                input(
                    type="search",
                    name="search_text",
                    placeholder="Search…",
                    on_blur=State.searchEdited,
                ),
            ),
        ),
    )
