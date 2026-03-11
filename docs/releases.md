# Release Log

Use one line per shipped change.

| Date | Branch | Commit | Type | Summary | AI Tool | AI Usage | Human Check | Validation | Client Impact | Rollback | Defect Found |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-11 | feat/travel-copilot-poc | uncommitted | docs | Added a simple product overview document describing the product, POC scope, future additions, and market gap. | codex | docs | self-verified | `uv run pytest -q` | Stakeholders now have a plain-language explainer for demos and product discussions. | Remove the overview doc and README reference. | None |
| 2026-03-11 | feat/travel-copilot-poc | uncommitted | feat | Added `.env` loading and a `.env.example` template for OpenAI and local database configuration. | codex | code | self-verified | `uv run pytest -q` | Developers can configure local credentials and DB path without editing source. | Remove env loader, example file, and README note. | None |
| 2026-03-11 | feat/travel-copilot-poc | uncommitted | feat | Added a Streamlit travel-planning POC with seeded demo data, policy/ranking logic, approval-gated exports, and documented that Snyk scan could not be completed because the MCP call was rejected. | codex | code | self-verified | `uv run pytest -q`; manual smoke of generation/export | Demo users can generate and export a human-reviewed road-trip packet in one flow. | Remove new app files and revert README/release entry. | None |
