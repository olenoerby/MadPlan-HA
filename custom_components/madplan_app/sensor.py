"""Sensors for the day's food, the shopping list, the pantry, votes, buying and the budget."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MadPlanConfigEntry
from .coordinator import MadPlanCoordinator
from .entity import MadPlanEntity

CURRENCY = "DKK"


@dataclass(frozen=True, kw_only=True)
class MadPlanSensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]
    attributes: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _budget(summary: dict[str, Any], period: str, field: str) -> Any:
    return (summary.get(f"budget_{period}") or {}).get(field)


SENSORS: tuple[MadPlanSensorDescription, ...] = (
    MadPlanSensorDescription(
        key="dinner_today",
        icon="mdi:silverware-fork-knife",
        value=lambda s: s.get("today_dinner"),
        attributes=lambda s: {"meals": s.get("today_meals", [])},
    ),
    MadPlanSensorDescription(
        key="next_meal",
        icon="mdi:food",
        value=lambda s: (s.get("next_meal") or {}).get("title"),
        attributes=lambda s: {k: v for k, v in (s.get("next_meal") or {}).items() if k != "title"},
    ),
    MadPlanSensorDescription(
        key="shopping_remaining",
        icon="mdi:cart",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: s.get("shopping_remaining"),
    ),
    MadPlanSensorDescription(
        key="shopping_cost",
        icon="mdi:cash",
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        value=lambda s: s.get("shopping_cost"),
    ),
    MadPlanSensorDescription(
        key="expiring",
        icon="mdi:timer-sand",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: s.get("expiring_count"),
        attributes=lambda s: {"items": s.get("expiring", [])},
    ),
    MadPlanSensorDescription(
        key="running_low",
        icon="mdi:basket-unfill",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: len(s.get("running_low") or []),
        attributes=lambda s: {"items": s.get("running_low", [])},
    ),
    MadPlanSensorDescription(
        key="buy_now",
        icon="mdi:cart-arrow-down",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: len(s.get("buy_now") or []),
        attributes=lambda s: {"items": s.get("buy_now", [])},
    ),
    MadPlanSensorDescription(
        key="meals_to_vote",
        icon="mdi:vote",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: len(s.get("meals_to_vote") or []),
        attributes=lambda s: {"meals": s.get("meals_to_vote", [])},
    ),
    MadPlanSensorDescription(
        key="meals_not_sent",
        icon="mdi:send-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: len(s.get("mealie_unsent") or []),
        attributes=lambda s: {"meals": s.get("mealie_unsent", [])},
    ),
    MadPlanSensorDescription(
        key="budget_week_expected",
        icon="mdi:calendar-week",
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        value=lambda s: _budget(s, "week", "expected"),
        attributes=lambda s: {
            "budget": _budget(s, "week", "budget"),
            "remaining": _budget(s, "week", "remaining"),
            "over_budget": _budget(s, "week", "over_budget"),
            "spent": _budget(s, "week", "spent"),
        },
    ),
    MadPlanSensorDescription(
        key="budget_month_expected",
        icon="mdi:calendar-month",
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        value=lambda s: _budget(s, "month", "expected"),
        attributes=lambda s: {
            "budget": _budget(s, "month", "budget"),
            "remaining": _budget(s, "month", "remaining"),
            "over_budget": _budget(s, "month", "over_budget"),
            "spent": _budget(s, "month", "spent"),
        },
    ),
    MadPlanSensorDescription(
        key="savings_year",
        icon="mdi:piggy-bank",
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        value=lambda s: s.get("savings_year"),
    ),
    MadPlanSensorDescription(
        key="price_alerts",
        icon="mdi:tag-heart",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: len(s.get("alerts") or []),
        attributes=lambda s: {"alerts": s.get("alerts", [])},
    ),
    MadPlanSensorDescription(
        key="notifications",
        icon="mdi:bell",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda s: s.get("unread_notifications"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: MadPlanConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(MadPlanSensor(entry.runtime_data, description) for description in SENSORS)


class MadPlanSensor(MadPlanEntity, SensorEntity):
    platform_domain = "sensor"
    entity_description: MadPlanSensorDescription

    def __init__(self, coordinator: MadPlanCoordinator, description: MadPlanSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data.summary)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attributes = self.entity_description.attributes
        return attributes(self.coordinator.data.summary) if attributes else None
