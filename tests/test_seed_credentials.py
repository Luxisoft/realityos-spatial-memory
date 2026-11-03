"""Demo setup must never create accounts with a shared default password."""

import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize("password", [None, "", "too-short"])
def test_seed_requires_private_password_before_accessing_database(
    monkeypatch, password
):
    path = Path(__file__).resolve().parents[1] / "scripts/seed_demo.py"
    spec = importlib.util.spec_from_file_location("seed_credentials", path)
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    if password is None:
        monkeypatch.delenv("SEED_ADMIN_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("SEED_ADMIN_PASSWORD", password)

    def unexpected_database_access():
        pytest.fail(
            "Missing seed credentials must fail before reading runtime settings"
        )

    monkeypatch.setattr(seed, "get_settings", unexpected_database_access)
    with pytest.raises(ValueError, match="SEED_ADMIN_PASSWORD"):
        seed.main()
