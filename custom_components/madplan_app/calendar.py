"""The meal plan as a calendar in Home Assistant."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from . import MadPlanConfigEntry
from .api import MadPlanError
from .entity import MadPlanEntity


def _to_event(meal: dict[str, Any]) -> CalendarEvent:
    day = date.fromisoformat(meal["date"])
    return CalendarEvent(
        start=day,
        end=day + timedelta(days=1),
        summary=meal["title"],
        description=meal["meal_type"],
        uid=str(meal["id"]),
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: MadPlanConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([MadPlanCalendar(entry.runtime_data, "meal_plan")])


class MadPlanCalendar(MadPlanEntity, CalendarEntity):
    platform_domain = "calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """The next meal, today or later."""
        today = dt_util.now().date().isoformat()
        for meal in self.coordinator.data.meals:
            if meal["date"] >= today:
                return _to_event(meal)
        return None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        try:
            meals = await self.coordinator.client.calendar(start_date.date(), end_date.date())
        except MadPlanError as exc:
            raise UpdateFailed(str(exc)) from exc
        return [_to_event(meal) for meal in meals]
