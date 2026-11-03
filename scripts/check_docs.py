"""Check localized documentation, local links/anchors and catalog coverage offline."""

import argparse
import html
import posixpath
import re
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
REPO_URLS = (
    "https://github.com/Luxisoft/realityos-spatial-memory/blob/main/",
    "https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/",
)


def prose(text):
    """Exclude fenced examples while preserving source line numbers."""
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker and fence is None:
            fence = marker[1]
        elif marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
            fence = None
            result.append("\n")
            continue
        result.append("\n" if fence else line)
    return "".join(result)


def links(text):
    patterns = (
        r"\]\((?:<([^>]+)>|([^\s)]+))",
        r"""\b(?:href|src)=["']([^"']+)["']""",
        r"(?m)^\[[^\]]+\]:\s*(?:<([^>]+)>|([^\s]+))",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            yield (
                next(group for group in match.groups() if group),
                text.count("\n", 0, match.start()) + 1,
            )


def anchors(text):
    ids = set(re.findall(r"""\bid=["']([^"']+)["']""", text))
    counts = Counter()
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text):
        heading = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", heading)
        heading = html.unescape(re.sub(r"<[^>]+>", "", heading)).lower()
        slug = "".join(
            char
            for char in heading
            if char in " _-" or unicodedata.category(char)[0] in "LNM"
        ).replace(" ", "-")
        ids.add(slug + (f"-{counts[slug]}" if counts[slug] else ""))
        counts[slug] += 1
    return ids


def local_target(source, value):
    value = html.unescape(value)
    for prefix in REPO_URLS:
        if value.startswith(prefix):
            value = "/" + value[len(prefix) :]
            break
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return None
    if not parts.path:
        target = source
    elif parts.path.startswith("/"):
        target = ROOT / unquote(parts.path).lstrip("/")
    else:
        target = source.parent / unquote(parts.path)
    return target.resolve(), unquote(parts.fragment)


def root_readme():
    """Publish the canonical English overview at the root with working links."""
    text = (ROOT / "docs/en/README.md").read_text()

    def rebase(value):
        parts = urlsplit(value)
        if parts.scheme or parts.netloc or not parts.path:
            return value
        path = posixpath.normpath(posixpath.join("docs/en", parts.path))
        return urlunsplit(("", "", path, parts.query, parts.fragment))

    def replace(match):
        value = match[1]
        start, end = match.span(1)
        offset = match.start()
        return match[0][: start - offset] + rebase(value) + match[0][end - offset :]

    text = re.sub(r"\]\(([^\s)]+)\)", replace, text)
    text = re.sub(r"""\b(?:href|src)=["']([^"']+)["']""", replace, text)
    return (
        "<!-- Generated from docs/en/README.md. Edit the EN/ES originals, then run "
        "python3 scripts/check_docs.py --sync-readme. -->\n\n" + text
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-readme", action="store_true")
    args = parser.parse_args()
    expected_readme = root_readme()
    if args.sync_readme:
        (ROOT / "README.md").write_text(expected_readme)
    documents = sorted((ROOT / "docs").rglob("*.md")) + [
        ROOT / name for name in ("README.md", "AGENTS.md", "MUSE.md")
    ]
    contents = {path.resolve(): prose(path.read_text()) for path in documents}
    ids = {path: anchors(text) for path, text in contents.items()}
    errors, checked = [], 0
    if (ROOT / "README.md").read_text() != expected_readme:
        errors.append(
            "README.md: out of sync with docs/en/README.md; "
            "run python3 scripts/check_docs.py --sync-readme"
        )
    tracked = {
        (ROOT / path).resolve()
        for path in subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
        ).split("\0")
        if path and (ROOT / path).exists()
    }
    for path in tracked:
        if path.suffix == ".md" and path not in contents:
            errors.append(
                f"{path.relative_to(ROOT)}: Markdown outside the language catalogs/tool entry points"
            )
    for source, text in contents.items():
        for value, line in links(text):
            location = f"{source.relative_to(ROOT)}:{line}"
            result = local_target(source, value)
            if result is None:
                continue
            target, fragment = result
            checked += 1
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"{location}: missing local target {value}")
            elif target.is_file() and target not in tracked:
                errors.append(
                    f"{location}: target is ignored or unavailable in Git {value}"
                )
            elif (
                target.suffix == ".md"
                and fragment
                and fragment not in ids.get(target, set())
            ):
                errors.append(f"{location}: missing anchor {value}")
    languages = {}
    for lang in ("en", "es"):
        home = ROOT / "docs" / lang
        pages = set(home.rglob("*.md"))
        languages[lang] = {page.relative_to(home) for page in pages}
        catalog = {
            result[0]
            for value, _ in links(contents[home / "INDEX.md"])
            if (result := local_target(home / "INDEX.md", value)) is not None
        }
        for page in pages:
            if page.name.endswith((".es.md", ".legacy.md")):
                errors.append(f"{page.relative_to(ROOT)}: obsolete naming")
            if page.name not in {"INDEX.md", "README.md"} and page not in catalog:
                errors.append(f"{page.relative_to(ROOT)}: missing from language index")
    if languages["en"] != languages["es"]:
        errors.append("Language catalogs do not contain matching documents")
    expected = {ROOT / "docs/README.md"} | {
        ROOT / "docs" / lang / page
        for lang, pages in languages.items()
        for page in pages
    }
    if set((ROOT / "docs").rglob("*.md")) != expected:
        errors.append(
            "Documentation must live in docs/en or docs/es, except docs/README.md"
        )
    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"PASS: {len(documents)} Markdown files, {checked} local links and anchors; matching EN/ES catalogs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
