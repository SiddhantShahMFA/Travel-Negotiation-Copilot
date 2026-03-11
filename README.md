# Travel-Negotiation-Copilot

Streamlit proof of concept for a human-in-the-loop sports travel planning copilot. The demo uses seeded NBA-style data to generate a three-city road trip plan with deterministic policy checks, transparent vendor ranking, grounded draft outreach, approval gates, and exportable itinerary packets.

For a plain-language product summary, see [docs/product-overview.md](/Users/siddhantshah/Desktop/AI/Travel-Negotiation-Copilot/docs/product-overview.md).

## What the POC does

- Seeds one domestic three-city road trip for the fictional Pacific Waves team.
- Parses the schedule into trip legs and travel windows.
- Applies travel policy rules for hotel ceilings, aircraft preferences, curfew, and recovery windows.
- Ranks hotel and charter vendors using explicit scoring factors.
- Retrieves relevant policy, template, and historical trip snippets to ground outputs.
- Drafts a recommendation, outreach emails, and itinerary with an OpenAI model when `OPENAI_API_KEY` is present.
- Falls back to deterministic drafts when no model credentials are configured.
- Requires approval of recommendation, outreach, and itinerary before export.
- Exports one Markdown packet and one HTML packet.

## Tech stack

- Python 3.14
- Streamlit
- SQLite
- OpenAI Python SDK
- `uv` for environment management
- `pytest` for automated verification

## Local setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e . pytest
```

Optional environment variables:

- `OPENAI_API_KEY`: enables live LLM drafting.
- `OPENAI_MODEL`: overrides the default model name used by the drafting service.
- `APP_DB_PATH`: overrides the local SQLite file path.

You can copy the reference file and fill in local values:

```bash
cp .env.example .env
```

The app loads `.env` automatically on startup and before draft generation.

## Run the app

```bash
uv run streamlit run app.py
```

Use the sidebar to adjust party size and curfew, then generate the scenario. The UI shows trip legs, constraints, risks, ranked vendors, grounded snippets, draft outputs, and export controls.

## Test the project

```bash
uv run pytest -q
```

## Demo scenario

The seeded demo covers:

- Los Angeles to Denver
- Denver to Phoenix on a back-to-back
- Phoenix to San Antonio after a late-night departure

The recommended “wow moment” is to change the party size or curfew in the sidebar and regenerate the packet to show how the outreach and itinerary update immediately.

## Current limitations

- Seeded demo data only; no CSV or PDF upload flow yet
- No outbound email sending
- No quote-entry workflow
- No vendor portal integrations
- Security scan was attempted but could not be completed because the Snyk MCP tool call was rejected in-session
