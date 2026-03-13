"""Governed pricing and freight sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PricingSource:
    def __init__(self, pricing_path: Path, freight_path: Path) -> None:
        self.pricing_path = pricing_path
        self.freight_path = freight_path

    def _read_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_product(self, product_code: str) -> dict[str, Any] | None:
        return self._read_json(self.pricing_path).get("products", {}).get(product_code)

    def get_freight_per_unit(self, destination_port: str | None) -> float:
        freight_data = self._read_json(self.freight_path)
        default_value = float(freight_data.get("default_freight_per_unit", 0))
        if not destination_port:
            return default_value
        return float(freight_data.get("ports", {}).get(destination_port.lower(), default_value))
