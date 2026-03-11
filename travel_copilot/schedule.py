from __future__ import annotations

from datetime import datetime, timedelta

from .models import Trip


def parse_schedule(schedule: dict, party_size: int) -> list[Trip]:
    games = schedule["games"]
    trips: list[Trip] = []

    for index, game in enumerate(games):
        game_dt = datetime.fromisoformat(game["game_datetime"])
        next_dt = (
            datetime.fromisoformat(games[index + 1]["game_datetime"])
            if index + 1 < len(games)
            else None
        )

        if next_dt is None:
            nights = 1
        else:
            gap_days = (next_dt.date() - game_dt.date()).days
            nights = max(1, gap_days - 1)

        departure_target = game_dt - timedelta(hours=22)
        hotel_checkout = game_dt + timedelta(hours=17)
        travel_windows = {
            "departure_target": departure_target.isoformat(),
            "hotel_checkin_target": (departure_target + timedelta(hours=3)).isoformat(),
            "game_time_local": game_dt.isoformat(),
            "postgame_departure_target": (game_dt + timedelta(hours=2, minutes=50)).isoformat(),
            "hotel_checkout_target": hotel_checkout.isoformat(),
        }

        trips.append(
            Trip(
                trip_id=game["trip_id"],
                opponent=game["opponent"],
                city=game["city"],
                game_datetime=game["game_datetime"],
                party_size=party_size,
                nights=nights,
                special_requirements=game["special_requirements"],
                travel_windows=travel_windows,
            )
        )

    return trips
