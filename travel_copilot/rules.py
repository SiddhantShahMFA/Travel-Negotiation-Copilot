from __future__ import annotations

from datetime import datetime, time

from .models import Policy, Trip


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def evaluate_policy(trips: list[Trip], policy: Policy) -> tuple[list[str], list[str]]:
    constraints = [
        f"Hotel ceiling is ${policy.max_hotel_rate:.0f} per room night before exceptions.",
        f"Preferred aircraft types: {', '.join(policy.aircraft_preferences)}.",
        f"Standard curfew is {policy.curfew} local unless approved otherwise.",
    ]
    risk_log: list[str] = []
    curfew = _parse_clock(policy.curfew)
    late_arrival_threshold = policy.recovery_windows["late_arrival_min_hours"]
    back_to_back_threshold = policy.recovery_windows["back_to_back_buffer_hours"]

    for index, trip in enumerate(trips):
        postgame_departure = datetime.fromisoformat(
            trip.travel_windows["postgame_departure_target"]
        )
        if _is_curfew_breach(postgame_departure.time(), curfew):
            risk_log.append(
                f"{trip.city}: projected postgame departure {postgame_departure.strftime('%H:%M')} breaches curfew {policy.curfew}."
            )

        if index + 1 < len(trips):
            next_game = datetime.fromisoformat(trips[index + 1].game_datetime)
            arrival_estimate = postgame_departure + _transfer_time_hours(trip.city, trips[index + 1].city)
            recovery_hours = (next_game - arrival_estimate).total_seconds() / 3600

            if recovery_hours < late_arrival_threshold:
                risk_log.append(
                    f"{trips[index + 1].city}: only {recovery_hours:.1f} recovery hours after late arrival; target is {late_arrival_threshold}+."
                )

            if (next_game - datetime.fromisoformat(trip.game_datetime)).total_seconds() / 3600 < back_to_back_threshold:
                risk_log.append(
                    f"{trip.city} to {trips[index + 1].city}: back-to-back travel window is below {back_to_back_threshold} hours."
                )

    return constraints, risk_log


def _transfer_time_hours(origin: str, destination: str):
    hours = {
        ("Denver", "Phoenix"): 2.1,
        ("Phoenix", "San Antonio"): 2.3,
    }.get((origin, destination), 2.0)
    from datetime import timedelta

    return timedelta(hours=hours)


def _is_curfew_breach(departure: time, curfew: time) -> bool:
    if curfew.hour < 6:
        return departure.hour < 12 and departure > curfew
    return departure > curfew
