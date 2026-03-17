import importlib.util
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _load_app_module():
    app_spec = importlib.util.spec_from_file_location("travel_copilot_app", APP_PATH)
    assert app_spec is not None
    assert app_spec.loader is not None
    app_module = importlib.util.module_from_spec(app_spec)
    app_spec.loader.exec_module(app_module)
    return app_module


def test_metric_card_helper_contains_expected_content(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app_module = _load_app_module()
    card = app_module._metric_card_html("Trip legs", "3", "Three-city road run")

    assert '<div class="metric-card">' in card
    assert "Trip legs" in card
    assert "3" in card
    assert "Three-city road run" in card


def test_kpi_cards_render_without_leaking_raw_html(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("OPENAI_API_KEY", "")

    app_test = AppTest.from_file(str(APP_PATH))
    app_test.default_timeout = 40

    app_test.run()
    app_test.button[0].click()
    app_test.run(timeout=40)

    html_blocks = app_test.get("html")
    markdown_values = [getattr(element, "value", "") for element in app_test.markdown]
    content_markdown = [value for value in markdown_values if not value.lstrip().startswith("<style>")]

    assert len(html_blocks) == 5
    assert any("Trip Overview" in value for value in markdown_values)
    assert all("metric-card" not in value for value in content_markdown)
    assert all("metric-strip" not in value for value in content_markdown)
