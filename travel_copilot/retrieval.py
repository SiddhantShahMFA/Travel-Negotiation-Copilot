from __future__ import annotations

import re
from collections import Counter

from .models import Policy, Trip, Vendor


def build_documents(
    policy: Policy,
    history: list[dict],
    templates: list[dict],
    vendors: list[Vendor],
) -> list[dict[str, str]]:
    documents = [
        {
            "source": "policy",
            "text": (
                f"Hotel cap {policy.max_hotel_rate}, curfew {policy.curfew}, "
                f"aircraft {'/'.join(policy.aircraft_preferences)}, exceptions {'; '.join(policy.exceptions)}"
            ),
        }
    ]

    documents.extend(
        {"source": "history", "text": item["note"]} for item in history
    )
    documents.extend(
        {"source": f"template:{item['category']}", "text": item["text"]}
        for item in templates
    )
    documents.extend(
        {"source": f"vendor:{vendor.vendor_id}", "text": vendor.notes}
        for vendor in vendors
    )
    return documents


def retrieve_relevant_snippets(
    trips: list[Trip], documents: list[dict[str, str]], top_k: int = 6
) -> list[dict[str, str]]:
    query = " ".join(
        [trip.city for trip in trips]
        + [requirement for trip in trips for requirement in trip.special_requirements]
    )
    query_tokens = Counter(_tokenize(query))
    scored: list[tuple[int, dict[str, str]]] = []

    for document in documents:
        doc_tokens = Counter(_tokenize(document["text"]))
        overlap = sum((query_tokens & doc_tokens).values())
        if overlap:
            scored.append((overlap, document))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {"source": document["source"], "snippet": document["text"]}
        for _, document in scored[:top_k]
    ]


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())
