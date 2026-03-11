from __future__ import annotations

from .models import Policy, RankedVendor, Trip, Vendor


def rank_hotels(
    trips: list[Trip], vendors: list[Vendor], policy: Policy
) -> dict[str, list[RankedVendor]]:
    hotel_vendors = [vendor for vendor in vendors if vendor.category == "hotel"]
    rankings: dict[str, list[RankedVendor]] = {}

    for trip in trips:
        matches = [vendor for vendor in hotel_vendors if vendor.city == trip.city]
        scored = [
            _score_hotel(vendor=vendor, trip=trip, policy=policy)
            for vendor in matches
        ]
        rankings[trip.trip_id] = sorted(scored, key=lambda item: item.score, reverse=True)

    return rankings


def rank_charters(
    trips: list[Trip], vendors: list[Vendor], policy: Policy
) -> list[RankedVendor]:
    charter_vendors = [vendor for vendor in vendors if vendor.category == "charter"]
    scored = [
        _score_charter(vendor=vendor, trip_count=len(trips), policy=policy)
        for vendor in charter_vendors
    ]
    return sorted(scored, key=lambda item: item.score, reverse=True)


def _score_hotel(vendor: Vendor, trip: Trip, policy: Policy) -> RankedVendor:
    reasons: list[str] = []
    score = 100.0

    preference_bonus = max(0, 12 - vendor.preferred_rank * 3)
    score += preference_bonus
    reasons.append(f"Preferred rank #{vendor.preferred_rank}.")

    score += vendor.historical_win_rate * 18
    reasons.append(f"Historical win rate {vendor.historical_win_rate:.0%}.")

    response_bonus = max(0, 10 - vendor.historical_response_time * 2)
    score += response_bonus
    reasons.append(f"Average response time {vendor.historical_response_time:.1f}h.")

    if vendor.rate_card is not None and vendor.rate_card <= policy.max_hotel_rate:
        score += 8
        reasons.append(
            f"Rate card ${vendor.rate_card:.0f} is within policy ceiling ${policy.max_hotel_rate:.0f}."
        )
    else:
        score -= 12
        reasons.append("Rate card is above policy ceiling or unavailable.")

    notes_lower = vendor.notes.lower()
    requirement_hit = sum(
        1
        for requirement in trip.special_requirements
        if any(token in notes_lower for token in requirement.lower().split() if len(token) > 4)
    )
    score += requirement_hit * 4
    if requirement_hit:
        reasons.append("Historical notes align with current trip requirements.")

    return RankedVendor(vendor=vendor, score=round(score, 2), reasons=reasons)


def _score_charter(vendor: Vendor, trip_count: int, policy: Policy) -> RankedVendor:
    reasons: list[str] = []
    score = 100.0

    preference_bonus = max(0, 15 - vendor.preferred_rank * 4)
    score += preference_bonus
    reasons.append(f"Preferred rank #{vendor.preferred_rank}.")

    score += vendor.historical_win_rate * 20
    reasons.append(f"Historical win rate {vendor.historical_win_rate:.0%}.")

    response_bonus = max(0, 10 - vendor.historical_response_time * 2)
    score += response_bonus
    reasons.append(f"Average response time {vendor.historical_response_time:.1f}h.")

    notes_lower = vendor.notes.lower()
    if any(aircraft.lower() in notes_lower for aircraft in policy.aircraft_preferences):
        score += 8
        reasons.append("Aircraft notes align with team preference.")

    if vendor.rate_card is not None and vendor.rate_card <= policy.approval_thresholds["charter_total"]:
        score += 6
        reasons.append("Indicative charter cost fits under approval threshold.")
    else:
        score -= 6
        reasons.append("Indicative charter cost likely needs extra approval.")

    score += trip_count * 1.5
    reasons.append(f"Scored for a {trip_count}-leg road trip workload.")

    return RankedVendor(vendor=vendor, score=round(score, 2), reasons=reasons)
