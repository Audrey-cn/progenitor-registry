import ast
import sys

from repo_paths import PROTOCOL_DIR, TRAE_DIR

ALLOWED_THIRD_PARTY = set()
LOCAL_MODULES = {"engine", "incubator", "hatchery", "stargate_identity", "stargate_transport"}


def imported_roots(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main():
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    stdlib.update({"__future__"})

    targets = list((PROTOCOL_DIR / "hatchery").glob("*.py"))
    violations = []
    for path in targets:
        for root in sorted(imported_roots(path)):
            if root in stdlib or root in LOCAL_MODULES or root in ALLOWED_THIRD_PARTY:
                continue
            violations.append((path, root))

    print("=" * 60)
    print("  Progenitor Dependency Check")
    print("=" * 60)
    print(f"  scanned files: {len(targets)}")

    if not violations:
        print("  OK: hatchery uses Python standard library only")
        return 0

    for path, root in violations:
        rel = path.relative_to(TRAE_DIR)
        print(f"  ERROR: {rel} imports non-stdlib module '{root}'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
