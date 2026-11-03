"""Retirement must preserve the native Display API and both installation realms."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_has_api_ingress_without_browser_services():
    for name in ("docker-compose.yml", "docker-compose.local.yml"):
        config = yaml.safe_load((ROOT / "infrastructure" / name).read_text())
        services = config["services"]
        assert set(services) == {
            "api",
            "worker",
            "proxy",
            "postgres",
            "redis",
            "scheduler",
        }
        assert "beat" in services["scheduler"]["command"]
        assert "api" in services["proxy"]["depends_on"]
    for name in ("default.conf", "local.conf"):
        config = (ROOT / "infrastructure/nginx" / name).read_text()
        assert "location /v1/" in config and "location /health/" in config
        for path in ("/docs", "/docs/oauth2-redirect"):
            assert f"location = {path} {{ proxy_pass http://api:8000; }}" in config
        assert "location / { return 410; }" in config
        assert "location /display/ { return 410; }" in config
        assert "http://frontend" not in config and "http://display" not in config


def test_api_documentation_uses_the_public_contract_after_web_retirement(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "url: '/v1/openapi.json'" in response.text
    assert "SwaggerUIBundle" in response.text
    assert client.get("/docs/oauth2-redirect").status_code == 200
    assert client.get("/v1/openapi.json").status_code == 200


def test_ci_keeps_android_gateway_and_api_without_web_builds():
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert "web" not in ci["jobs"]
    assert {"android", "backend", "meta-gateway"} <= ci["jobs"].keys()
    deploy = (ROOT / ".github/workflows/deploy-production.yml").read_text()
    assert "build frontend display" not in deploy
    assert "scripts/deploy/retire_web.py" in deploy
    assert "infrastructure/gateway/docker-compose.yml" in deploy
