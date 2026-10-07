import pytest


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDPILOT_DB_PATH", str(tmp_path / "history.db"))
