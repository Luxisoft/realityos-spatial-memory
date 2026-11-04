"""Enforce module boundaries, database authority and source-size limits."""

from pathlib import Path

from architecture_rules import architecture_issues

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = {"backend/app/faces.py", "tests/test_faces.py"}
ROOTS = (
    "backend",
    "meta-gateway",
    "tests",
    "gateway-tests",
    "android/app/src",
    "scripts",
)


def main() -> int:
    violations = architecture_issues(ROOT)
    for directory in ROOTS:
        for path in sorted((ROOT / directory).rglob("*")):
            if not path.is_file() or path.suffix not in {
                ".py",
                ".ts",
                ".tsx",
                ".css",
                ".kt",
                ".kts",
                ".sh",
                ".sql",
                ".html",
            }:
                continue
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            count = len(path.read_text().splitlines())
            if count >= 1000 and relative not in PROTECTED:
                violations.append(f"{relative}: {count} lines (maximum 999)")
    if violations:
        print("\n".join(violations))
        return 1
    print("Architecture boundaries, database authority and source-size limits passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
