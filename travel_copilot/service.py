from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .demo_data import (
    load_history,
    load_placeholder_quotes,
    load_policy,
    load_schedule,
    load_templates,
    load_vendors,
)
from .drafting import build_output_packet
from .models import Policy, ScenarioPlan
from .ranking import rank_charters, rank_hotels
from .retrieval import build_documents, retrieve_relevant_snippets
from .rules import evaluate_policy
from .schedule import parse_schedule
from .storage import initialize_database


def generate_plan(
    db_path: Path,
    party_size: int = 54,
    curfew: str = "01:00",
) -> ScenarioPlan:
    schedule = load_schedule()
    policy = load_policy()
    vendors = load_vendors()
    history = load_history()
    templates = load_templates()
    quotes = load_placeholder_quotes()

    policy = _apply_policy_overrides(policy, curfew=curfew)
    trips = parse_schedule(schedule, party_size=party_size)
    initialize_database(db_path=db_path, trips=trips, policy=policy, vendors=vendors, quotes=quotes)

    constraints, risk_log = evaluate_policy(trips=trips, policy=policy)
    hotel_rankings = rank_hotels(trips=trips, vendors=vendors, policy=policy)
    charter_rankings = rank_charters(trips=trips, vendors=vendors, policy=policy)
    documents = build_documents(policy=policy, history=history, templates=templates, vendors=vendors)
    source_snippets = retrieve_relevant_snippets(trips=trips, documents=documents)
    packet = build_output_packet(
        team_name=schedule["team_name"],
        league=schedule["league"],
        trips=trips,
        policy=policy,
        hotel_rankings=hotel_rankings,
        charter_rankings=charter_rankings,
        constraints=constraints,
        risk_log=risk_log,
        source_snippets=source_snippets,
    )

    return ScenarioPlan(
        scenario_id=schedule["scenario_id"],
        team_name=schedule["team_name"],
        league=schedule["league"],
        trips=trips,
        policy=policy,
        hotel_rankings=hotel_rankings,
        charter_rankings=charter_rankings,
        constraints=constraints,
        risk_log=risk_log,
        source_snippets=source_snippets,
        output_packet=packet,
    )


def _apply_policy_overrides(policy: Policy, curfew: str) -> Policy:
    overridden = deepcopy(policy)
    overridden.curfew = curfew
    return overridden
