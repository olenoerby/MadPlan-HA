"""The shopping list as a to-do list in Home Assistant."""

from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MadPlanConfigEntry
from .api import MadPlanError
from .entity import MadPlanEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: MadPlanConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([MadPlanShoppingList(entry.runtime_data, "shopping_list")])


class MadPlanShoppingList(MadPlanEntity, TodoListEntity):
    platform_domain = "todo"
    _attr_supported_features = TodoListEntityFeature.CREATE_TODO_ITEM | TodoListEntityFeature.UPDATE_TODO_ITEM

    @property
    def todo_items(self) -> list[TodoItem]:
        items = []
        for item in self.coordinator.data.shopping.get("items", []):
            quantity = f"{item['quantity']:g} {item.get('unit') or ''}".strip() if item.get("quantity") else ""
            store = item.get("store") or ""
            description = " · ".join(part for part in (quantity, store) if part) or None
            items.append(
                TodoItem(
                    uid=str(item["id"]),
                    summary=item["name"],
                    description=description,
                    status=TodoItemStatus.COMPLETED if item.get("checked") else TodoItemStatus.NEEDS_ACTION,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        try:
            await self.coordinator.client.add_item(item.summary or "")
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        try:
            await self.coordinator.client.set_item_checked(int(item.uid), item.status == TodoItemStatus.COMPLETED)
        except MadPlanError as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_refresh()
