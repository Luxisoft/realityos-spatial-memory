"""No deployment or local installation can build a resident speech model."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deployment_contains_only_backend_and_gateway_images():
    workflow = (ROOT / ".github/workflows/deploy-production.yml").read_text()
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    local = (ROOT / "infrastructure/docker-compose.local.yml").read_text()
    for content in (workflow, ci, local):
        for retired in ("seamless", "infrastructure/tts", "REALITYOS_TTS_IMAGE"):
            assert retired not in content
    assert "file: backend/Dockerfile" in workflow
    assert "file: meta-gateway/Dockerfile" in workflow
    assert "ELEVENLABS_API_KEY" in (ROOT / ".env.local.example").read_text()
    assert not (ROOT / "backend/app/providers/seamless_service.py").exists()


def test_speech_failure_does_not_stop_the_local_database_or_api():
    startup = (ROOT / "scripts/local/Start-RealityOS.ps1").read_text()
    assert "@('stop')" not in startup
    assert "Read-LocalSecret 'Clave ElevenLabs propia" in startup
