"""Execute the production reconciliation branch against a recording Docker stub."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "provider,enabled,exists",
    [
        ("elevenlabs", "false", True),
        ("elevenlabs", "true", True),
        ("elevenlabs", "false", False),
        ("seamless", "true", True),
        ("seamless", "false", True),
    ],
)
def test_deployment_only_starts_explicit_local_speech(
    tmp_path, provider, enabled, exists
):
    workflow = Path(".github/workflows/deploy-production.yml").read_text()
    start = workflow.index('            if grep -qx "TTS_LOCAL_ENABLED=true" .env')
    branch = workflow[start : workflow.index("            # Browser apps", start)]
    (tmp_path / ".env").write_text(
        f"TTS_PROVIDER={provider}\nTTS_LOCAL_ENABLED={enabled}\n"
    )
    (tmp_path / "sudo").write_text('#!/bin/sh\nexec "$@"\n')
    (tmp_path / "docker").write_text(
        "#!/bin/sh\n"
        'if [ "$1 $2" = "container inspect" ]; then exit "$EXISTS_STATUS"; fi\n'
        'printf "%s\\n" "$*" >> "$DOCKER_CALLS"\n'
    )
    for name in ("sudo", "docker"):
        (tmp_path / name).chmod(0o700)
    calls = tmp_path / "calls"
    subprocess.run(
        ["bash", "-eu", "-c", branch],
        cwd=tmp_path,
        check=True,
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "DOCKER_CALLS": str(calls),
            "EXISTS_STATUS": "0" if exists else "1",
            "runtime_overlay": "preserved.json",
        },
    )
    recorded = calls.read_text() if calls.exists() else ""
    if provider == "seamless" and enabled == "true":
        assert "--profile speech pull seamless-tts" in recorded
        assert "--profile speech up" in recorded
        assert "stop" not in recorded
    elif exists:
        assert recorded.splitlines() == [
            "update --restart=no infrastructure-seamless-tts-1",
            "stop infrastructure-seamless-tts-1",
        ]
    else:
        assert not recorded
