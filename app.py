from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from travel_copilot.config import load_env_file
from travel_copilot.drafting import approvals_complete
from travel_copilot.exporter import build_html_export, build_markdown_export
from travel_copilot.service import generate_plan
from travel_copilot.storage import load_settings, save_output_packet, save_settings


load_env_file()
DB_PATH = Path(os.getenv("APP_DB_PATH", "data/app.db"))


def main() -> None:
    st.set_page_config(page_title="Travel Negotiation Copilot", layout="wide")
    st.title("Travel Negotiation Copilot")
    st.caption("Human-in-the-loop POC for one-team domestic travel planning.")

    stored_settings = load_settings(DB_PATH)
    default_party_size = int(stored_settings.get("party_size", 54))
    default_curfew = stored_settings.get("curfew", "01:00")

    st.sidebar.header("Scenario Controls")
    st.sidebar.write("Scenario: Pacific Waves 3-city road trip")
    party_size = st.sidebar.number_input(
        "Travel party size",
        min_value=40,
        max_value=80,
        value=default_party_size,
        step=1,
    )
    curfew = st.sidebar.selectbox(
        "Curfew policy",
        options=["00:30", "01:00", "01:30", "02:00"],
        index=["00:30", "01:00", "01:30", "02:00"].index(default_curfew)
        if default_curfew in ["00:30", "01:00", "01:30", "02:00"]
        else 1,
    )

    if st.sidebar.button("Generate trip plan", use_container_width=True):
        plan = generate_plan(db_path=DB_PATH, party_size=int(party_size), curfew=curfew)
        st.session_state["plan"] = plan
        st.session_state["approvals"] = dict(plan.output_packet.approval_status)
        save_settings(DB_PATH, {"party_size": int(party_size), "curfew": curfew})
        save_output_packet(DB_PATH, plan.output_packet)

    plan = st.session_state.get("plan")
    if not plan:
        st.info("Generate the demo scenario to review rankings, drafts, and exportable itinerary output.")
        return

    st.subheader("Trip Overview")
    for trip in plan.trips:
        with st.expander(f"{trip.city} vs {trip.opponent}", expanded=True):
            st.write(f"Game time: `{trip.game_datetime}`")
            st.write(f"Nights: `{trip.nights}`")
            st.write(f"Party size: `{trip.party_size}`")
            st.write("Travel windows:")
            for key, value in trip.travel_windows.items():
                st.write(f"- `{key}`: {value}")
            st.write("Special requirements:")
            for requirement in trip.special_requirements:
                st.write(f"- {requirement}")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Constraints")
        for item in plan.constraints:
            st.write(f"- {item}")
    with right:
        st.subheader("Risk Log")
        for risk in plan.risk_log or ["No critical risks detected."]:
            st.write(f"- {risk}")

    st.subheader("Ranked Hotel Options")
    for trip in plan.trips:
        st.markdown(f"**{trip.city}**")
        for ranked in plan.hotel_rankings[trip.trip_id]:
            st.markdown(f"- `{ranked.score}` {ranked.vendor.name}")
            for reason in ranked.reasons:
                st.caption(reason)

    st.subheader("Ranked Charter Options")
    for ranked in plan.charter_rankings:
        st.markdown(f"- `{ranked.score}` {ranked.vendor.name}")
        for reason in ranked.reasons:
            st.caption(reason)

    st.subheader("Source Snippets")
    for item in plan.source_snippets:
        with st.expander(item["source"]):
            st.write(item["snippet"])

    packet = plan.output_packet
    st.subheader("AI Drafts")
    recommendation_tab, outreach_tab, itinerary_tab = st.tabs(
        ["Recommendation", "Outreach", "Itinerary"]
    )
    with recommendation_tab:
        st.markdown(packet.recommendation)
    with outreach_tab:
        for name, draft in packet.outreach_drafts.items():
            st.markdown(f"**{name.replace('_', ' ').title()}**")
            st.code(draft)
    with itinerary_tab:
        st.markdown(packet.itinerary)
        st.markdown("**Negotiation Summary**")
        st.markdown(packet.negotiation_summary)

    st.subheader("Approvals")
    approvals = st.session_state.get("approvals", dict(packet.approval_status))
    recommendation_ok = st.checkbox(
        "Recommendation approved",
        value=approvals.get("recommendation", False),
    )
    outreach_ok = st.checkbox(
        "Outreach drafts approved",
        value=approvals.get("outreach", False),
    )
    itinerary_ok = st.checkbox(
        "Itinerary approved",
        value=approvals.get("itinerary", False),
    )

    packet.approval_status = {
        "recommendation": recommendation_ok,
        "outreach": outreach_ok,
        "itinerary": itinerary_ok,
    }
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
        )
        st.download_button(
            "Download HTML packet",
            html_export,
            file_name="travel_packet.html",
            mime="text/html",
        )
    else:
        st.warning("Approve recommendation, outreach, and itinerary before exporting.")


if __name__ == "__main__":
    main()
