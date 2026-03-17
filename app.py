from __future__ import annotations

import os
from html import escape
from pathlib import Path

import streamlit as st

from travel_copilot.config import load_env_file
from travel_copilot.drafting import approvals_complete
from travel_copilot.exporter import build_html_export, build_markdown_export
from travel_copilot.models import OutputPacket, RankedVendor, ScenarioPlan, Trip
from travel_copilot.service import generate_plan
from travel_copilot.storage import load_settings, save_output_packet, save_settings


load_env_file()
DB_PATH = Path(os.getenv("APP_DB_PATH", "data/app.db"))
CURFEW_OPTIONS = ["00:30", "01:00", "01:30", "02:00"]
APPROVAL_SECTIONS = ("recommendation", "outreach", "itinerary")


def main() -> None:
    st.set_page_config(page_title="Travel Negotiation Copilot", layout="wide")
    _render_styles()

    stored_settings = load_settings(DB_PATH)
    default_party_size = int(stored_settings.get("party_size", 54))
    default_curfew = stored_settings.get("curfew", "01:00")

    party_size, curfew, should_generate = _render_sidebar(
        default_party_size=default_party_size,
        default_curfew=default_curfew,
    )

    if should_generate:
        plan = generate_plan(db_path=DB_PATH, party_size=int(party_size), curfew=curfew)
        approvals = dict(plan.output_packet.approval_status)
        st.session_state["plan"] = plan
        st.session_state["approvals"] = approvals
        _set_approval_widget_state(approvals)
        save_settings(DB_PATH, {"party_size": int(party_size), "curfew": curfew})
        save_output_packet(DB_PATH, plan.output_packet)

    plan = st.session_state.get("plan")
    _render_hero(plan=plan, party_size=int(party_size), curfew=curfew)

    if not plan:
        _render_empty_state()
        return

    _initialize_approval_widget_state(plan.output_packet)
    approvals = _current_approvals(plan.output_packet)

    _render_metric_strip(plan=plan, approvals=approvals)

    overview_tab, vendors_tab, packet_tab = st.tabs(
        ["Overview", "Vendors", "Packet & Approvals"]
    )
    with overview_tab:
        _render_overview_tab(plan=plan)
    with vendors_tab:
        _render_vendors_tab(plan=plan)
    with packet_tab:
        _render_packet_tab(plan=plan)


def _render_sidebar(default_party_size: int, default_curfew: str) -> tuple[int, str, bool]:
    st.sidebar.markdown("### Scenario Controls")
    st.sidebar.markdown("Pacific Waves three-city road trip")
    st.sidebar.caption("Tune the demo variables, then regenerate the full packet.")

    party_size = st.sidebar.number_input(
        "Travel party size",
        min_value=40,
        max_value=80,
        value=default_party_size,
        step=1,
    )
    curfew = st.sidebar.selectbox(
        "Curfew policy",
        options=CURFEW_OPTIONS,
        index=CURFEW_OPTIONS.index(default_curfew)
        if default_curfew in CURFEW_OPTIONS
        else 1,
    )

    st.sidebar.markdown(
        """
        <div class="sidebar-note">
            <strong>Demo flow</strong><br/>
            Generate the plan, review risks and rankings, approve each draft, then export the packet.
        </div>
        """,
        unsafe_allow_html=True,
    )
    should_generate = st.sidebar.button("Generate trip plan", use_container_width=True)
    return int(party_size), curfew, should_generate


def _render_hero(plan: ScenarioPlan | None, party_size: int, curfew: str) -> None:
    if plan:
        approvals = _current_approvals(plan.output_packet)
        approval_count = sum(approvals.values())
        status_label = "Packet live"
        status_detail = f"{approval_count}/3 approvals complete"
        generated_at = plan.output_packet.generated_at
    else:
        status_label = "Ready for generation"
        status_detail = "Generate a packet to unlock rankings, drafts, and exports"
        generated_at = "No packet generated yet"

    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">Pacific Waves Operations Command</div>
                    <h1>Travel Negotiation Copilot</h1>
                    <p class="hero-copy">
                        Premium demo dashboard for building a three-city road trip packet with transparent vendor scoring,
                        grounded drafts, and human approval gates.
                    </p>
                    <div class="chip-row">
                        <span class="status-chip accent">NBA Demo</span>
                        <span class="status-chip">{party_size} travelers</span>
                        <span class="status-chip">Curfew {escape(curfew)}</span>
                    </div>
                </div>
                <div class="hero-panel">
                    <div class="eyebrow">Live Scenario</div>
                    <div class="hero-panel-title">Denver · Phoenix · San Antonio</div>
                    <div class="hero-panel-copy">Status: {escape(status_label)}</div>
                    <div class="hero-panel-copy">{escape(status_detail)}</div>
                    <div class="hero-panel-copy">Generated: {escape(generated_at)}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_empty_state() -> None:
    st.markdown(
        """
        <div class="section-header">
            <div class="eyebrow">Launch Sequence</div>
            <h2>Generate the road-trip packet to fill the dashboard</h2>
            <p>
                The app already has seeded schedule, policy, vendor, and history data. Use the sidebar controls to
                spin up a polished demo packet in one step.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="empty-grid">
            <div class="empty-card">
                <div class="empty-card-title">1. Set the scenario</div>
                <p>Adjust party size and curfew to show how policy and draft outputs react to operational constraints.</p>
            </div>
            <div class="empty-card">
                <div class="empty-card-title">2. Review the board</div>
                <p>Scan trips, risks, vendor rankings, and grounded snippets from a single premium dashboard layout.</p>
            </div>
            <div class="empty-card">
                <div class="empty-card-title">3. Approve and export</div>
                <p>Clear the approval gates before downloading the itinerary packet as Markdown or HTML.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metric_strip(plan: ScenarioPlan, approvals: dict[str, bool]) -> None:
    metrics = [
        ("Trip legs", str(len(plan.trips)), "Three-city road run"),
        ("Party size", str(plan.trips[0].party_size), "Shared across all trip legs"),
        ("Curfew", plan.policy.curfew, "Active policy override"),
        ("Risk count", str(len(plan.risk_log)), "Operational flags requiring review"),
        (
            "Approval progress",
            f"{sum(approvals.values())}/{len(APPROVAL_SECTIONS)}",
            "Recommendation, outreach, itinerary",
        ),
    ]
    metric_columns = st.columns(len(metrics))
    for column, (label, value, detail) in zip(metric_columns, metrics, strict=False):
        with column:
            st.html(_metric_card_html(label=label, value=value, detail=detail))


def _render_overview_tab(plan: ScenarioPlan) -> None:
    _render_section_header(
        title="Trip Overview",
        description="Compact leg-by-leg cards surface the schedule, windows, and special handling requirements.",
    )

    trip_columns = st.columns(len(plan.trips))
    for column, trip in zip(trip_columns, plan.trips, strict=False):
        with column:
            st.markdown(_trip_card_html(trip), unsafe_allow_html=True)

    _render_section_header(
        title="Constraints And Risks",
        description="Policy boundaries stay visible while risk items get stronger emphasis for faster review.",
    )
    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            _list_card_html(
                title="Constraints",
                items=plan.constraints,
                tone="neutral",
                empty_message="No active constraints detected.",
            ),
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            _list_card_html(
                title="Risk Log",
                items=plan.risk_log,
                tone="danger",
                empty_message="No critical risks detected.",
            ),
            unsafe_allow_html=True,
        )

    _render_section_header(
        title="Grounding Snippets",
        description="Source context stays visible in dedicated tabs so the recommendation still feels grounded during demos.",
    )
    snippet_tabs = st.tabs([item["source"] for item in plan.source_snippets])
    for tab, item in zip(snippet_tabs, plan.source_snippets, strict=False):
        with tab:
            st.markdown(_snippet_card_html(item["source"], item["snippet"]), unsafe_allow_html=True)


def _render_vendors_tab(plan: ScenarioPlan) -> None:
    _render_section_header(
        title="Hotel Rankings",
        description="Ranked hotel cards keep score, explanation, and vendor performance signals in the same visual frame.",
    )
    for trip in plan.trips:
        st.markdown(
            f"""
            <div class="subsection-banner">
                <div class="eyebrow">Hotel board</div>
                <h3>{escape(trip.city)} vs {escape(trip.opponent)}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        hotel_columns = st.columns(len(plan.hotel_rankings[trip.trip_id]))
        for column, ranked in zip(hotel_columns, plan.hotel_rankings[trip.trip_id], strict=False):
            with column:
                st.markdown(_vendor_card_html(ranked), unsafe_allow_html=True)

    _render_section_header(
        title="Charter Rankings",
        description="Charter choices use the same score-driven presentation so commercial tradeoffs are easy to compare.",
    )
    charter_columns = st.columns(len(plan.charter_rankings))
    for column, ranked in zip(charter_columns, plan.charter_rankings, strict=False):
        with column:
            st.markdown(_vendor_card_html(ranked), unsafe_allow_html=True)


def _render_packet_tab(plan: ScenarioPlan) -> None:
    packet = plan.output_packet
    draft_column, approval_column = st.columns([1.55, 0.85])

    with draft_column:
        _render_section_header(
            title="AI Drafts",
            description="Draft content stays grouped by output type while reducing the wall-of-text feel during walkthroughs.",
        )
        recommendation_tab, outreach_tab, itinerary_tab = st.tabs(
            ["Recommendation", "Outreach", "Itinerary"]
        )
        with recommendation_tab:
            st.markdown(packet.recommendation)
        with outreach_tab:
            draft_names = list(packet.outreach_drafts.keys())
            outreach_tabs = st.tabs([name.replace("_", " ").title() for name in draft_names])
            for outreach_tab_item, name in zip(outreach_tabs, draft_names, strict=False):
                with outreach_tab_item:
                    st.code(packet.outreach_drafts[name], language="text")
        with itinerary_tab:
            st.markdown(packet.itinerary)
            st.markdown("#### Negotiation Summary")
            st.markdown(packet.negotiation_summary)

    with approval_column:
        approvals = _current_approvals(packet)
        st.markdown(
            _approval_summary_html(sum(approvals.values()), len(APPROVAL_SECTIONS)),
            unsafe_allow_html=True,
        )

        st.checkbox("Recommendation approved", key=_approval_key("recommendation"))
        st.checkbox("Outreach drafts approved", key=_approval_key("outreach"))
        st.checkbox("Itinerary approved", key=_approval_key("itinerary"))

        packet.approval_status = _current_approvals(packet)
        st.session_state["approvals"] = dict(packet.approval_status)
        save_output_packet(DB_PATH, packet)

        if approvals_complete(packet):
            st.success("All approval gates are complete. Export is enabled.")
            markdown_export = build_markdown_export(plan)
            html_export = build_html_export(plan)
            st.download_button(
                "Download Markdown packet",
                markdown_export,
                file_name="travel_packet.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                "Download HTML packet",
                html_export,
                file_name="travel_packet.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.warning("Approve recommendation, outreach, and itinerary before exporting.")


def _set_approval_widget_state(approvals: dict[str, bool]) -> None:
    for section in APPROVAL_SECTIONS:
        st.session_state[_approval_key(section)] = approvals.get(section, False)


def _initialize_approval_widget_state(packet: OutputPacket) -> None:
    stored = st.session_state.get("approvals", dict(packet.approval_status))
    for section in APPROVAL_SECTIONS:
        key = _approval_key(section)
        if key not in st.session_state:
            st.session_state[key] = stored.get(section, False)


def _current_approvals(packet: OutputPacket) -> dict[str, bool]:
    stored = st.session_state.get("approvals", dict(packet.approval_status))
    return {
        section: bool(st.session_state.get(_approval_key(section), stored.get(section, False)))
        for section in APPROVAL_SECTIONS
    }


def _approval_key(section: str) -> str:
    return f"approval_{section}"


def _render_section_header(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <div class="eyebrow">Dashboard Section</div>
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _metric_card_html(label: str, value: str, detail: str) -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div>'
        f'<div class="metric-detail">{escape(detail)}</div>'
        f"</div>"
    )


def _trip_card_html(trip: Trip) -> str:
    windows = "".join(
        f"<li><span>{escape(key.replace('_', ' ').title())}</span><strong>{escape(value)}</strong></li>"
        for key, value in trip.travel_windows.items()
    )
    requirements = "".join(
        f"<li>{escape(requirement)}</li>" for requirement in trip.special_requirements
    )
    return f"""
        <div class="trip-card">
            <div class="eyebrow">Trip Leg</div>
            <div class="trip-title">{escape(trip.city)}</div>
            <div class="trip-subtitle">vs {escape(trip.opponent)}</div>
            <div class="chip-row">
                <span class="status-chip accent">{trip.nights} nights</span>
                <span class="status-chip">{trip.party_size} travelers</span>
            </div>
            <div class="trip-meta">
                <span class="meta-label">Game Time</span>
                <span>{escape(trip.game_datetime)}</span>
            </div>
            <div class="card-divider"></div>
            <div class="card-section-label">Travel Windows</div>
            <ul class="detail-list compact">{windows}</ul>
            <div class="card-section-label">Special Requirements</div>
            <ul class="bullet-list">{requirements}</ul>
        </div>
    """


def _list_card_html(title: str, items: list[str], tone: str, empty_message: str) -> str:
    rows = "".join(f"<li>{escape(item)}</li>" for item in items) or f"<li>{escape(empty_message)}</li>"
    return f"""
        <div class="info-card {escape(tone)}">
            <div class="eyebrow">Operational Readout</div>
            <div class="info-card-title">{escape(title)}</div>
            <ul class="bullet-list spaced">{rows}</ul>
        </div>
    """


def _snippet_card_html(source: str, snippet: str) -> str:
    return f"""
        <div class="snippet-card">
            <div class="eyebrow">Grounded Source</div>
            <div class="snippet-title">{escape(source)}</div>
            <p>{escape(snippet)}</p>
        </div>
    """


def _vendor_card_html(ranked: RankedVendor) -> str:
    reasons = "".join(f"<li>{escape(reason)}</li>" for reason in ranked.reasons)
    win_rate = f"{ranked.vendor.historical_win_rate * 100:.0f}%"
    response_time = f"{ranked.vendor.historical_response_time:.0f}h"
    return f"""
        <div class="vendor-card">
            <div class="vendor-card-top">
                <div>
                    <div class="eyebrow">{escape(ranked.vendor.category.title())} Vendor</div>
                    <div class="vendor-title">{escape(ranked.vendor.name)}</div>
                    <div class="vendor-subtitle">{escape(ranked.vendor.city)}</div>
                </div>
                <div class="score-pill">
                    <span class="score-label">Score</span>
                    <span class="score-value">{ranked.score:.2f}</span>
                </div>
            </div>
            <div class="vendor-stats">
                <div><span>Preferred rank</span><strong>{ranked.vendor.preferred_rank}</strong></div>
                <div><span>Win rate</span><strong>{win_rate}</strong></div>
                <div><span>Response time</span><strong>{response_time}</strong></div>
            </div>
            <div class="card-divider"></div>
            <div class="card-section-label">Why it scored here</div>
            <ul class="bullet-list">{reasons}</ul>
        </div>
    """


def _approval_summary_html(approved_count: int, total_count: int) -> str:
    progress = int((approved_count / total_count) * 100) if total_count else 0
    return f"""
        <div class="approval-card">
            <div class="eyebrow">Approval Console</div>
            <div class="approval-title">Packet Release Status</div>
            <p>{approved_count} of {total_count} required approvals are complete.</p>
            <div class="approval-progress">
                <div class="approval-progress-bar" style="width: {progress}%;"></div>
            </div>
            <div class="chip-row">
                <span class="status-chip accent">{progress}% complete</span>
                <span class="status-chip">Exports unlock at {total_count}/{total_count}</span>
            </div>
        </div>
    """


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(38, 191, 255, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(255, 167, 76, 0.16), transparent 28%),
                linear-gradient(180deg, #07101f 0%, #0b1630 48%, #08111e 100%);
            color: #eef4ff;
        }
        .block-container {
            max-width: 1380px;
            padding-top: 2.1rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            font-family: "Futura", "Avenir Next", "Trebuchet MS", sans-serif;
            letter-spacing: 0.02em;
        }
        p, div, span, li, label {
            font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
        }
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(10, 19, 39, 0.96) 0%, rgba(8, 15, 30, 0.98) 100%);
            border-right: 1px solid rgba(120, 227, 255, 0.12);
        }
        [data-testid="stSidebar"] * {
            color: #f4f7ff;
        }
        [data-testid="stSidebar"] .stNumberInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(18, 32, 61, 0.92);
            border: 1px solid rgba(120, 227, 255, 0.18);
            border-radius: 14px;
        }
        .sidebar-note {
            margin: 1rem 0 1.1rem;
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: linear-gradient(160deg, rgba(13, 25, 49, 0.95), rgba(18, 42, 78, 0.88));
            border: 1px solid rgba(120, 227, 255, 0.14);
            color: #d8e7ff;
            line-height: 1.5;
        }
        .stButton > button,
        .stDownloadButton > button {
            border: none;
            border-radius: 999px;
            background: linear-gradient(135deg, #1cb4ff 0%, #0f79ff 55%, #0e5bd3 100%);
            color: white;
            font-weight: 700;
            letter-spacing: 0.01em;
            box-shadow: 0 10px 24px rgba(7, 67, 140, 0.35);
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, #35bfff 0%, #2f8dff 55%, #216ce6 100%);
        }
        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        [data-testid="stTabs"] [role="tab"] {
            border-radius: 999px;
            background: rgba(16, 31, 59, 0.78);
            border: 1px solid rgba(120, 227, 255, 0.12);
            padding: 0.45rem 1rem;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            background: rgba(120, 227, 255, 0.16);
            border-color: rgba(120, 227, 255, 0.42);
        }
        .hero-shell,
        .metric-card,
        .trip-card,
        .info-card,
        .snippet-card,
        .vendor-card,
        .approval-card,
        .empty-card {
            border: 1px solid rgba(120, 227, 255, 0.14);
            box-shadow: 0 22px 48px rgba(4, 10, 22, 0.28);
        }
        .hero-shell {
            padding: 1.6rem 1.75rem;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(9, 20, 41, 0.96), rgba(17, 46, 85, 0.9)),
                linear-gradient(45deg, rgba(28, 180, 255, 0.2), rgba(255, 167, 76, 0.12));
            margin-bottom: 1.4rem;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.65fr) minmax(290px, 0.9fr);
            gap: 1rem;
            align-items: end;
        }
        .hero-copy {
            max-width: 48rem;
            color: #d6e6ff;
            font-size: 1.05rem;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .hero-panel {
            padding: 1.15rem 1.2rem;
            border-radius: 22px;
            background: rgba(8, 18, 36, 0.72);
            border: 1px solid rgba(120, 227, 255, 0.14);
        }
        .hero-panel-title,
        .trip-title,
        .info-card-title,
        .approval-title,
        .snippet-title,
        .vendor-title,
        .empty-card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #f7fbff;
        }
        .hero-panel-copy,
        .trip-subtitle,
        .vendor-subtitle,
        .section-header p,
        .empty-card p {
            color: #c7d7f4;
            line-height: 1.55;
        }
        .eyebrow,
        .card-section-label,
        .metric-label,
        .meta-label,
        .score-label {
            color: #7fdfff;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }
        .status-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.42rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #eaf1ff;
            font-size: 0.88rem;
        }
        .status-chip.accent {
            background: rgba(120, 227, 255, 0.15);
            border-color: rgba(120, 227, 255, 0.28);
        }
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.9rem;
            margin-bottom: 0.5rem;
        }
        .metric-card {
            border-radius: 22px;
            padding: 1rem 1.05rem;
            background: rgba(8, 18, 36, 0.78);
        }
        .metric-value {
            color: #ffffff;
            font-size: 1.85rem;
            font-weight: 800;
            margin: 0.2rem 0 0.25rem;
        }
        .metric-detail {
            color: #a8bddf;
            line-height: 1.45;
        }
        .section-header {
            margin: 1.6rem 0 0.95rem;
        }
        .section-header h2,
        .subsection-banner h3 {
            margin: 0.15rem 0 0.25rem;
            color: #f8fbff;
        }
        .subsection-banner {
            margin: 1rem 0 0.8rem;
            padding: 0.25rem 0;
        }
        .trip-card,
        .info-card,
        .snippet-card,
        .vendor-card,
        .approval-card,
        .empty-card {
            border-radius: 24px;
            background: rgba(8, 18, 36, 0.8);
            padding: 1.15rem 1.15rem 1.05rem;
            height: 100%;
        }
        .trip-meta {
            margin-top: 0.9rem;
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
            color: #dbe7fb;
        }
        .card-divider {
            border-top: 1px solid rgba(120, 227, 255, 0.12);
            margin: 1rem 0 0.85rem;
        }
        .detail-list,
        .bullet-list {
            list-style: none;
            padding: 0;
            margin: 0.65rem 0 0;
        }
        .detail-list li,
        .bullet-list li {
            display: flex;
            justify-content: space-between;
            gap: 0.9rem;
            padding: 0.48rem 0;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            color: #dde8fa;
        }
        .detail-list li:first-child,
        .bullet-list li:first-child {
            border-top: none;
            padding-top: 0;
        }
        .bullet-list li {
            display: block;
            line-height: 1.55;
        }
        .bullet-list.spaced li {
            padding: 0.6rem 0;
        }
        .compact li strong {
            text-align: right;
        }
        .info-card.danger {
            background: linear-gradient(180deg, rgba(44, 15, 28, 0.9), rgba(29, 10, 20, 0.92));
            border-color: rgba(255, 122, 138, 0.28);
        }
        .snippet-card p {
            color: #dde7fa;
            line-height: 1.65;
            margin-top: 0.7rem;
        }
        .vendor-card-top {
            display: flex;
            justify-content: space-between;
            gap: 0.9rem;
            align-items: start;
        }
        .score-pill {
            min-width: 92px;
            padding: 0.65rem 0.75rem;
            border-radius: 18px;
            background: rgba(255, 167, 76, 0.12);
            border: 1px solid rgba(255, 167, 76, 0.24);
            text-align: right;
        }
        .score-value {
            display: block;
            font-size: 1.65rem;
            font-weight: 800;
            color: #ffd2a1;
        }
        .vendor-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.95rem;
        }
        .vendor-stats div {
            padding: 0.7rem 0.75rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.04);
        }
        .vendor-stats span {
            display: block;
            color: #90a8ce;
            font-size: 0.78rem;
            margin-bottom: 0.2rem;
        }
        .vendor-stats strong {
            color: #f3f8ff;
        }
        .approval-card {
            margin-bottom: 1rem;
        }
        .approval-progress {
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin: 0.85rem 0 1rem;
        }
        .approval-progress-bar {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #1cb4ff 0%, #5de2b3 100%);
        }
        .empty-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .empty-card {
            min-height: 190px;
        }
        .stAlert {
            border-radius: 18px;
        }
        .stCodeBlock,
        pre {
            border-radius: 18px !important;
            background: rgba(7, 17, 34, 0.94) !important;
            border: 1px solid rgba(120, 227, 255, 0.14);
        }
        @media (max-width: 1100px) {
            .hero-grid,
            .metric-strip,
            .empty-grid,
            .vendor-stats {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 900px) {
            .hero-grid,
            .metric-strip,
            .empty-grid,
            .vendor-stats {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
