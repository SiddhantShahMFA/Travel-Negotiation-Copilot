from pathlib import Path

from travel_copilot.drafting import approvals_complete
from travel_copilot.service import generate_plan


def test_parser_produces_expected_trip_legs(tmp_path: Path) -> None:
    plan = generate_plan(db_path=tmp_path / "app.db")

    assert [trip.city for trip in plan.trips] == ["Denver", "Phoenix", "San Antonio"]
    assert plan.trips[0].travel_windows["departure_target"].startswith("2026-01-13T21:00:00")
    assert plan.trips[1].nights == 2


def test_rules_emit_back_to_back_and_late_arrival_risks(tmp_path: Path) -> None:
    plan = generate_plan(db_path=tmp_path / "app.db")

    joined = " ".join(plan.risk_log)
    assert "breaches curfew" in joined
    assert "recovery hours" in joined


def test_rankings_are_stable_and_explainable(tmp_path: Path) -> None:
    plan = generate_plan(db_path=tmp_path / "app.db")

    denver_top = plan.hotel_rankings["TRIP-DEN-001"][0]
    charter_top = plan.charter_rankings[0]
    assert denver_top.vendor.vendor_id == "HOTEL-DEN-ALPINE"
    assert charter_top.vendor.vendor_id == "CHARTER-JETSTREAM"
    assert any("Preferred rank" in reason for reason in denver_top.reasons)


def test_fallback_drafts_are_grounded_and_do_not_invent_quotes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    plan = generate_plan(db_path=tmp_path / "app.db")

    assert plan.output_packet.recommendation.startswith("NON-LLM FALLBACK")
    combined = " ".join(plan.output_packet.outreach_drafts.values()) + plan.output_packet.negotiation_summary
    assert "pricing assumptions" in combined or "quotes" in combined
    assert "$999" not in combined


def test_approval_gate_requires_all_sections(tmp_path: Path) -> None:
    plan = generate_plan(db_path=tmp_path / "app.db")

    assert approvals_complete(plan.output_packet) is False
    plan.output_packet.approval_status = {
        "recommendation": True,
        "outreach": True,
        "itinerary": True,
    }
    assert approvals_complete(plan.output_packet) is True


def test_regeneration_changes_outputs_when_controls_change(tmp_path: Path) -> None:
    first = generate_plan(db_path=tmp_path / "first.db", party_size=54, curfew="01:00")
    second = generate_plan(db_path=tmp_path / "second.db", party_size=60, curfew="00:30")

    assert first.trips[0].party_size == 54
    assert second.trips[0].party_size == 60
    assert first.policy.curfew == "01:00"
    assert second.policy.curfew == "00:30"
    assert first.output_packet.recommendation != second.output_packet.recommendation
