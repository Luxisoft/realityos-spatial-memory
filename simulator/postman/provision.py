"""Retired public-password setup; local evaluation uses the account selector."""


def provision(*args, **kwargs):
    raise ValueError("Retired: start the local installation and select an existing scenario account.")


if __name__ == "__main__":
    raise SystemExit("Use scripts/local/start.sh or Start-RealityOS.ps1; no public-password account is created.")
