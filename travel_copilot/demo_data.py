from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Policy, Quote, Vendor


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _load_json(filename: str) -> Any:
    return json.loads((DATA_DIR / filename).read_text())


def load_schedule() -> dict[str, Any]:
    return _load_json("schedule.json")


def load_policy() -> Policy:
    return Policy(**_load_json("policy.json"))


def load_vendors() -> list[Vendor]:
    return [Vendor(**item) for item in _load_json("vendors.json")]


def load_history() -> list[dict[str, Any]]:
    return _load_json("history.json")


def load_templates() -> list[dict[str, str]]:
    return _load_json("templates.json")


def load_placeholder_quotes() -> list[Quote]:
    return [
        Quote(
            vendor_id="TBD",
            trip_id="TRIP-DEN-001",
            price=None,
            terms="Manual quote entry deferred in v1.",
            hold_deadline=None,
            cancellation_policy="Pending vendor response.",
            notes="Schema placeholder only.",
        )
    ]
