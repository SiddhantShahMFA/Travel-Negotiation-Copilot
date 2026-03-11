from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Trip:
    trip_id: str
    opponent: str
    city: str
    game_datetime: str
    party_size: int
    nights: int
    special_requirements: list[str]
    travel_windows: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Policy:
    policy_id: str
    max_hotel_rate: float
    room_mix: dict[str, int]
    approval_thresholds: dict[str, float]
    aircraft_preferences: list[str]
    curfew: str
    recovery_windows: dict[str, int]
    exceptions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Vendor:
    vendor_id: str
    name: str
    category: str
    city: str
    preferred_rank: int
    contact: dict[str, str]
    historical_response_time: float
    historical_win_rate: float
    notes: str
    rate_card: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Quote:
    vendor_id: str
    trip_id: str
    price: float | None
    terms: str
    hold_deadline: str | None
    cancellation_policy: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OutputPacket:
    recommendation: str
    itinerary: str
    outreach_drafts: dict[str, str]
    negotiation_summary: str
    risk_log: list[str]
    approval_status: dict[str, bool]
    source_snippets: list[dict[str, str]]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedVendor:
    vendor: Vendor
    score: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["vendor"] = self.vendor.to_dict()
        return payload


@dataclass
class ScenarioPlan:
    scenario_id: str
    team_name: str
    league: str
    trips: list[Trip]
    policy: Policy
    hotel_rankings: dict[str, list[RankedVendor]]
    charter_rankings: list[RankedVendor]
    constraints: list[str]
    risk_log: list[str]
    source_snippets: list[dict[str, str]]
    output_packet: OutputPacket


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
