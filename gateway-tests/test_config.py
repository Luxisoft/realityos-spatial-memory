"""Gateway configuration never discovers another service's private environment."""

import pytest
from realityos_meta_gateway.config import GatewaySettings, get_settings
from realityos_meta_gateway.main import create_app


@pytest.fixture
def isolated_gateway_environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key in GatewaySettings.model_fields:
        monkeypatch.delenv(key.upper(), raising=False)
    monkeypatch.delenv("META_GATEWAY_ENV_FILE", raising=False)
    (tmp_path / ".env").write_text(
        "MODEL_API_KEY=unrelated-realityos-key\n"
        "META_GATEWAY_TOKEN=unrelated-realityos-gateway-token\n"
        "META_API_BASE_URL=https://unexpected.invalid/v1\n"
    )
    return tmp_path


def test_injected_gateway_variables_do_not_read_dotenv(
    isolated_gateway_environment, monkeypatch
):
    monkeypatch.setenv("MODEL_API_KEY", "gateway-injected-model-key")
    monkeypatch.setenv("META_GATEWAY_TOKEN", "gateway-injected-secret-token")
    settings = create_app().state.settings
    assert settings.model_api_key == "gateway-injected-model-key"
    assert settings.meta_gateway_token == "gateway-injected-secret-token"
    assert str(settings.meta_api_base_url) == "https://api.meta.ai/v1"


def test_explicit_gateway_file_preserves_environment_precedence(
    isolated_gateway_environment, monkeypatch
):
    selected = isolated_gateway_environment / "gateway.env"
    selected.write_text(
        "MODEL_API_KEY=explicit-gateway-model-key\n"
        "META_GATEWAY_TOKEN=explicit-gateway-secret-token\n"
    )
    monkeypatch.setenv("META_GATEWAY_ENV_FILE", str(selected))
    monkeypatch.setenv("MODEL_API_KEY", "gateway-injected-override-key")
    settings = get_settings()
    assert settings.model_api_key == "gateway-injected-override-key"
    assert settings.meta_gateway_token == "explicit-gateway-secret-token"
    assert str(settings.meta_api_base_url) == "https://api.meta.ai/v1"


def test_missing_selected_gateway_file_never_falls_back(
    isolated_gateway_environment, monkeypatch
):
    monkeypatch.setenv(
        "META_GATEWAY_ENV_FILE", str(isolated_gateway_environment / "missing.env")
    )
    with pytest.raises(FileNotFoundError, match="explicitly selected"):
        create_app()
