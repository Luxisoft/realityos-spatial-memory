"""Check module boundaries and prevent filesystem catalogs from becoming databases."""

import ast
import json
from pathlib import Path

# Their interfaces remain compatible; changing either protected arm is outside
# structural cleanup. Historical Alembic revisions are not scanned as app code.
PROTECTED_MODULES = {"app.faces", "app.face_setup"}
HTTP_COMPOSITION = {"app.routes", "app.runtime.routers"}
INSTALLATION_MODULES = {
    "app.local.bootstrap",
    "app.local.retirement",
    "app.local.sql_data",
    "app.local.social_bootstrap",
    "app.local.police_biometrics",
    "app.local.state",
    "app.local.upgrades",
    "app.runtime.schema",
}
RETIRED_CATALOGS = {"app.local_catalog", "app.local_seed", "app.local_display"}


def imports(tree: ast.AST, module: str):
    """Resolve aliases and relative imports, including imports inside functions."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for entry in node.names:
                yield node, entry.name, entry.asname or entry.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package = module.split(".")[: -node.level]
                base = ".".join([*package, *([base] if base else [])])
            for entry in node.names:
                yield node, f"{base}.{entry.name}", entry.asname or entry.name


def named(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return named(node.value) + "." + node.attr
    return ""


def under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def module_issues(module: str, source: str) -> list[tuple[int, str]]:
    if module in PROTECTED_MODULES:
        return []
    tree = ast.parse(source)
    aliases = {}
    issues = []

    def check_dependency(node, target):
        if under(target, "app.http") and not (
            under(module, "app.http") or module in HTTP_COMPOSITION
        ):
            issues.append(
                (node.lineno, "business modules must not import HTTP handlers")
            )
        if under(module, "app.providers") and under(target, "app.meta"):
            issues.append(
                (node.lineno, "providers must import provider contracts, not app.meta")
            )
        if any(under(target, old) for old in RETIRED_CATALOGS):
            issues.append((node.lineno, "retired filesystem catalogs are forbidden"))
        if module not in INSTALLATION_MODULES and any(
            under(target, installer) for installer in INSTALLATION_MODULES
        ):
            issues.append(
                (node.lineno, "operational modules must not import data initializers")
            )
        if under(target, "scripts") or under(target, "simulator"):
            issues.append(
                (
                    node.lineno,
                    "application modules must not import scripts or simulator",
                )
            )

    for node, target, alias in imports(tree, module):
        aliases[alias] = target
        check_dependency(node, target)

    bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bindings[node.target.id] = node.value

    def contains_json_path(node, visited=None):
        if node is None:
            return False
        visited = set() if visited is None else visited
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Constant)
                and isinstance(child.value, str)
                and child.value.casefold().endswith((".json", ".jsonl", ".ndjson"))
            ):
                return True
            if (
                isinstance(child, ast.Name)
                and child.id in bindings
                and child.id not in visited
                and contains_json_path(bindings[child.id], visited | {child.id})
            ):
                return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = named(node.func)
        first, _, suffix = function.partition(".")
        resolved = aliases.get(first, first) + ("." + suffix if suffix else "")
        if resolved in {"importlib.import_module", "__import__"} and node.args:
            argument = node.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                check_dependency(node, argument.value)
        if module == "app.providers.mock":
            continue  # Deterministic test provider, never the local/live runtime.
        if resolved == "json.load":
            issues.append(
                (node.lineno, "JSON file reads cannot supply application records")
            )
        is_read = (
            function.endswith((".read_text", ".read_bytes", ".open"))
            or function == "open"
        )
        if is_read and contains_json_path(node):
            issues.append(
                (node.lineno, "JSON file reads cannot supply application records")
            )
        if resolved == "json.loads" and any(
            isinstance(child, ast.Call)
            and named(child.func).endswith((".read_text", ".read_bytes", ".read"))
            for argument in node.args
            for child in ast.walk(argument)
        ):
            issues.append((node.lineno, "file-backed JSON catalogs are forbidden"))
    return sorted(set(issues))


def business_catalog(value) -> bool:
    if not isinstance(value, dict):
        return False
    if value.keys() & {
        "groups",
        "profiles",
        "publications",
        "records",
        "scenarios",
    }:
        return True
    accounts = value.get("accounts")
    if isinstance(accounts, list):
        return True
    if isinstance(accounts, dict) and any(
        isinstance(account, dict)
        and account.keys() & {"email", "display_name", "workspace_id"}
        for account in accounts.values()
    ):
        return True
    if (
        "batch" in value
        and isinstance(value["batch"], dict)
        and "records" in value["batch"]
    ):
        return True
    for item in value.get("items", []):
        if isinstance(item, dict) and item.keys() & {
            "caption",
            "owner",
            "post_id",
            "workspace_id",
            "category",
            "tags",
        }:
            return True
    return False


def architecture_issues(root: Path) -> list[str]:
    issues = []
    for path in sorted((root / "backend/app").rglob("*.py")):
        module = ".".join(path.relative_to(root / "backend").with_suffix("").parts)
        relative = path.relative_to(root).as_posix()
        if module in RETIRED_CATALOGS:
            issues.append(f"{relative}: retired filesystem catalog must be removed")
        for line, message in module_issues(module, path.read_text(encoding="utf-8")):
            issues.append(f"{relative}:{line}: {message}")
    for path in sorted((root / "simulator").rglob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if business_catalog(value):
            issues.append(
                f"{path.relative_to(root)}: business records belong in SQL initialization"
            )
    return issues
