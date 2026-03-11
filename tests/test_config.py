import os
from pathlib import Path

from travel_copilot.config import load_env_file


def test_load_env_file_sets_unset_values(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "OPENAI_API_KEY=test-key\nOPENAI_MODEL=test-model\nAPP_DB_PATH=data/custom.db\n"
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("APP_DB_PATH", raising=False)

    load_env_file(env_path)

    assert os.getenv("OPENAI_API_KEY") == "test-key"
    assert os.getenv("OPENAI_MODEL") == "test-model"
    assert os.getenv("APP_DB_PATH") == "data/custom.db"
