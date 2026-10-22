"""Semantic catalog model: Item, Product and composition are different concepts.

The existing InventoryItem remains the physical stock/cost master for backward
compatibility. These immutable value objects make the distinction explicit to
services and integrations while the database migration is introduced separately.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class _StringEnum(str, Enum):
    """Python 3.10-compatible equivalent of StrEnum's string behavior."""

    def __str__(self) -> str:
        return self.value


class ItemKind(_StringEnum):
    RAW_MATERIAL = "raw_material"
    PACKAGING = "packaging"
    TRADED = "traded"
    SEMI_FINISHED = "semi_finished"
    FINISHED = "finished"
    CONSUMABLE = "consumable"
    SERVICE = "service"


class ProductKind(_StringEnum):
    MANUFACTURED = "manufactured"
    TRADED = "traded"
    ASSEMBLED = "assembled"
    BUNDLE = "bundle"
    SERVICE = "service"


@dataclass(frozen=True)
class ItemRef:
    item_id: int
    kind: ItemKind


@dataclass(frozen=True)
class ProductRef:
    product_id: int
    kind: ProductKind
    inventory_item_id: int


@dataclass(frozen=True)
class CompositionLine:
    component_item_id: int
    quantity: Decimal
    waste_percentage: Decimal = Decimal("0")


@dataclass(frozen=True)
class ProductComposition:
    product_id: int
    lines: tuple[CompositionLine, ...]
    yield_quantity: Decimal = Decimal("1")

    def component_quantity(self, line: CompositionLine) -> Decimal:
        return line.quantity * (Decimal("1") + line.waste_percentage / Decimal("100"))

    def material_cost(self, unit_costs: dict[int, Decimal]) -> Decimal:
        total = Decimal("0")
        for line in self.lines:
            if line.component_item_id not in unit_costs:
                raise ValueError(f"Missing unit cost for item {line.component_item_id}")
            total += self.component_quantity(line) * unit_costs[line.component_item_id]
        return total / self.yield_quantity
