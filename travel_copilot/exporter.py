from __future__ import annotations

from html import escape

from .models import RankedVendor, ScenarioPlan


def build_markdown_export(plan: ScenarioPlan) -> str:
    packet = plan.output_packet
    lines = [
        f"# {plan.team_name} Travel Packet",
        "",
        f"Generated: {packet.generated_at}",
        "",
        "## Recommendation",
        packet.recommendation,
        "",
        "## Negotiation Summary",
        packet.negotiation_summary,
        "",
        "## Itinerary",
        packet.itinerary,
        "",
        "## Risk Log",
    ]
    lines.extend([f"- {risk}" for risk in packet.risk_log] or ["- None"])
    lines.extend(["", "## Ranked Hotels"])

    for trip in plan.trips:
        lines.append(f"### {trip.city}")
        for ranked in plan.hotel_rankings[trip.trip_id]:
            lines.append(f"- {ranked.vendor.name} ({ranked.score})")
            lines.extend([f"  - {reason}" for reason in ranked.reasons])

    lines.extend(["", "## Ranked Charter Options"])
    for ranked in plan.charter_rankings:
        lines.append(f"- {ranked.vendor.name} ({ranked.score})")
        lines.extend([f"  - {reason}" for reason in ranked.reasons])

    lines.extend(["", "## Outreach Drafts"])
    for key, value in packet.outreach_drafts.items():
        lines.extend([f"### {key.replace('_', ' ').title()}", value, ""])

    lines.extend(["## Source Snippets"])
    lines.extend(
        [f"- [{item['source']}] {item['snippet']}" for item in packet.source_snippets]
    )
    return "\n".join(lines)


def build_html_export(plan: ScenarioPlan) -> str:
    packet = plan.output_packet
    sections = [
        _section("Recommendation", packet.recommendation),
        _section("Negotiation Summary", packet.negotiation_summary),
        _section("Itinerary", packet.itinerary),
        _list_section("Risk Log", packet.risk_log),
        _ranked_hotels(plan),
        _ranked_charters(plan.charter_rankings),
        _outreach_section(packet.outreach_drafts),
        _snippets_section(packet.source_snippets),
    ]
    return (
        "<html><head><meta charset='utf-8'><title>Travel Packet</title>"
        "<style>body{font-family:Arial,sans-serif;margin:40px;line-height:1.5;}h1,h2,h3{color:#0f3557;}pre{white-space:pre-wrap;background:#f4f7fa;padding:16px;border-radius:8px;}li{margin-bottom:8px;}</style>"
        "</head><body>"
        f"<h1>{escape(plan.team_name)} Travel Packet</h1>"
        f"<p><strong>Generated:</strong> {escape(packet.generated_at)}</p>"
        + "".join(sections)
        + "</body></html>"
    )


def _section(title: str, body: str) -> str:
    return f"<h2>{escape(title)}</h2><pre>{escape(body)}</pre>"


def _list_section(title: str, items: list[str]) -> str:
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items) or "<li>None</li>"
    return f"<h2>{escape(title)}</h2><ul>{rendered}</ul>"


def _ranked_hotels(plan: ScenarioPlan) -> str:
    chunks = ["<h2>Ranked Hotels</h2>"]
    for trip in plan.trips:
        chunks.append(f"<h3>{escape(trip.city)}</h3><ul>")
        for ranked in plan.hotel_rankings[trip.trip_id]:
            chunks.append(f"<li><strong>{escape(ranked.vendor.name)}</strong> ({ranked.score})<ul>")
            chunks.extend(f"<li>{escape(reason)}</li>" for reason in ranked.reasons)
            chunks.append("</ul></li>")
        chunks.append("</ul>")
    return "".join(chunks)


def _ranked_charters(rankings: list[RankedVendor]) -> str:
    chunks = ["<h2>Ranked Charter Options</h2><ul>"]
    for ranked in rankings:
        chunks.append(f"<li><strong>{escape(ranked.vendor.name)}</strong> ({ranked.score})<ul>")
        chunks.extend(f"<li>{escape(reason)}</li>" for reason in ranked.reasons)
        chunks.append("</ul></li>")
    chunks.append("</ul>")
    return "".join(chunks)


def _outreach_section(outreach_drafts: dict[str, str]) -> str:
    chunks = ["<h2>Outreach Drafts</h2>"]
    for key, value in outreach_drafts.items():
        chunks.append(f"<h3>{escape(key.replace('_', ' ').title())}</h3><pre>{escape(value)}</pre>")
    return "".join(chunks)


def _snippets_section(snippets: list[dict[str, str]]) -> str:
    rendered = "".join(
        f"<li><strong>{escape(item['source'])}:</strong> {escape(item['snippet'])}</li>"
        for item in snippets
    )
    return f"<h2>Source Snippets</h2><ul>{rendered}</ul>"
