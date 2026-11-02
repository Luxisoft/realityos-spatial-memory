"""No deployment or local installation can build a resident speech model."""

from pathlib import Path


def test_deployment_contains_only_backend_and_gateway_images():
    workflow = Path(".github/workflows/deploy-production.yml").read_text()
    ci = Path(".github/workflows/ci.yml").read_text()
    local = Path("infrastructure/docker-compose.local.yml").read_text()
    for content in (workflow, ci, local):
        for retired in ("seamless", "infrastructure/tts", "REALITYOS_TTS_IMAGE"):
            assert retired not in content
    assert "file: backend/Dockerfile" in workflow
    assert "file: meta-gateway/Dockerfile" in workflow
    assert "ELEVENLABS_API_KEY" in Path(".env.local.example").read_text()
    assert not Path("backend/app/providers/seamless_service.py").exists()


def test_speech_failure_does_not_stop_the_local_database_or_api():
    startup = Path("scripts/local/Start-RealityOS.ps1").read_text()
    assert "@('stop')" not in startup
    assert "Read-LocalSecret 'Clave ElevenLabs propia" in startup
