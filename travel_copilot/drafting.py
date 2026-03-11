from __future__ import annotations

import json
import os
from typing import Any

from .config import load_env_file
from .models import OutputPacket, Policy, RankedVendor, Trip, utc_timestamp

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


SYSTEM_PROMPT = """You are a travel operations copilot for a professional sports team.
Only use facts provided in the input JSON.
Never invent prices, availability, contracts, or vendor commitments.
Draft concise, operations-ready content with clear caveats when information is pending."""


def build_output_packet(
    team_name: str,
    league: str,
    trips: list[Trip],
    policy: Policy,
    hotel_rankings: dict[str, list[RankedVendor]],
    charter_rankings: list[RankedVendor],
    constraints: list[str],
    risk_log: list[str],
    source_snippets: list[dict[str, str]],
) -> OutputPacket:
    context = {
        "team_name": team_name,
        "league": league,
        "trips": [trip.to_dict() for trip in trips],
        "policy": policy.to_dict(),
        "constraints": constraints,
        "risk_log": risk_log,
        "hotel_rankings": {
            trip_id: [item.to_dict() for item in ranked]
            for trip_id, ranked in hotel_rankings.items()
        },
        "charter_rankings": [item.to_dict() for item in charter_rankings],
        "source_snippets": source_snippets,
    }

    recommendation = _generate_text("recommendation", context)
    itinerary = _generate_text("itinerary", context)
    negotiation_summary = _generate_text("negotiation_summary", context)
    outreach_drafts = {
        "hotel_denver": _generate_text("hotel_outreach_denver", context),
        "hotel_phoenix": _generate_text("hotel_outreach_phoenix", context),
        "charter_master": _generate_text("charter_outreach", context),
    }

    return OutputPacket(
        recommendation=recommendation,
        itinerary=itinerary,
        outreach_drafts=outreach_drafts,
        negotiation_summary=negotiation_summary,
        risk_log=risk_log,
        approval_status={
            "recommendation": False,
            "outreach": False,
            "itinerary": False,
        },
        source_snippets=source_snippets,
        generated_at=utc_timestamp(),
    )


def approvals_complete(packet: OutputPacket) -> bool:
    return all(packet.approval_status.values())


def _generate_text(mode: str, context: dict[str, Any]) -> str:
    load_env_file()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if api_key and OpenAI is not None:
        prompt = _prompt_for_mode(mode, context)
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            if getattr(response, "output_text", None):
                return response.output_text.strip()
        except Exception:
            pass

    return _fallback_text(mode, context)


def _prompt_for_mode(mode: str, context: dict[str, Any]) -> str:
    instruction = {
        "recommendation": "Summarize the best charter and hotel plan, with ranked reasoning and explicit pending quote caveats.",
        "itinerary": "Draft a master itinerary for players, staff, and operations with timestamps and handoff notes.",
        "negotiation_summary": "Summarize negotiation asks and risks without inventing price or availability.",
        "hotel_outreach_denver": "Draft a hotel outreach email for the top-ranked Denver property requesting room block, meal room, recovery setup, late policy terms, and cancellation terms.",
        "hotel_outreach_phoenix": "Draft a hotel outreach email for the top-ranked Phoenix property requesting room block, postgame meal support, meeting space, and cancellation terms.",
        "charter_outreach": "Draft a charter outreach email for the top-ranked charter vendor requesting aircraft coverage, wheels-up timing, baggage handling, catering, and cancellation terms.",
    }[mode]
    return f"{instruction}\n\nInput JSON:\n{json.dumps(context, indent=2)}"


def _fallback_text(mode: str, context: dict[str, Any]) -> str:
    trips = context["trips"]
    policy = context["policy"]
    party_size = trips[0]["party_size"]
    charter = context["charter_rankings"][0]["vendor"]
    first_hotel = context["hotel_rankings"][trips[0]["trip_id"]][0]["vendor"]
    second_hotel = context["hotel_rankings"][trips[1]["trip_id"]][0]["vendor"]
    third_hotel = context["hotel_rankings"][trips[2]["trip_id"]][0]["vendor"]

    if mode == "recommendation":
        return (
            "NON-LLM FALLBACK\n"
            f"Recommend {charter['name']} as the charter lead for the three-city road trip because it is the highest-ranked option "
            f"and aligns best with aircraft preferences. Use {first_hotel['name']}, {second_hotel['name']}, and {third_hotel['name']} "
            f"as the first hotel outreach targets for a {party_size}-person travel party under a {policy['curfew']} curfew policy. "
            "Pricing and availability remain pending vendor confirmation. "
            f"Key risks: {'; '.join(context['risk_log']) if context['risk_log'] else 'none'}."
        )

    if mode == "itinerary":
        lines = ["NON-LLM FALLBACK", "Master itinerary overview:"]
        for trip in trips:
            lines.append(
                f"- {trip['city']}: depart target {trip['travel_windows']['departure_target']}, "
                f"game {trip['game_datetime']}, postgame departure target {trip['travel_windows']['postgame_departure_target']}, "
                f"party size {trip['party_size']}."
            )
        lines.append(
            f"Operations must confirm hotel rooming, meal rooms, and charter timing before release. Current curfew policy is {policy['curfew']}."
        )
        return "\n".join(lines)

    if mode == "negotiation_summary":
        return (
            "NON-LLM FALLBACK\n"
            "Negotiation focus: secure room blocks, suites, meal rooms, late checkout, aircraft assignment, baggage flow, and cancellation terms. "
            "Do not state or assume rates until the operators receive actual quotes."
        )

    if mode == "hotel_outreach_denver":
        return (
            "NON-LLM FALLBACK\n"
            f"Subject: Pacific Waves room block request for Denver trip\n\n"
            f"Hi {first_hotel['contact']['name']},\n\n"
            f"We are planning our January Denver stay for a {party_size}-person travel party and would like to request availability. "
            "Please confirm room block support, suite inventory, private postgame meal room access, recovery tub setup, late checkout options, and cancellation terms. "
            "We are not requesting pricing assumptions in this draft; our team will review actual quotes once received.\n\n"
            "Best,\nTravel Operations"
        )

    if mode == "hotel_outreach_phoenix":
        return (
            "NON-LLM FALLBACK\n"
            f"Subject: Pacific Waves postgame hotel request for Phoenix stop\n\n"
            f"Hi {second_hotel['contact']['name']},\n\n"
            f"Please help us scope a {party_size}-person team room block for our Phoenix game with late-arrival meal support, meeting room access, quiet-floor planning, and cancellation terms. "
            "We will review final quotes separately and are not including any assumed rates or holds in this draft.\n\n"
            "Best,\nTravel Operations"
        )

    return (
        "NON-LLM FALLBACK\n"
        f"Subject: Pacific Waves charter request for road trip coverage\n\n"
        f"Hi {charter['contact']['name']},\n\n"
        f"We are requesting charter support for a three-city road trip for {party_size} travelers. Please confirm aircraft coverage aligned to our preferred types, "
        "postgame wheels-up timing, baggage handling, catering timing, crew duty coverage, and cancellation terms. "
        "We will evaluate pricing only after receiving official quotes.\n\n"
        "Best,\nTravel Operations"
    )
