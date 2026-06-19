import argparse
import json
from pathlib import Path

from repo_paths import GIT_DIR, TRAE_DIR

META_FILE = GIT_DIR / "META.json"
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
MOJIBAKE_MARKERS = ["\ufffd", "Ã", "â", "å", "ç", "æ"]
PLACEHOLDER_MARKERS = ["????"]


def iter_declared_text_files():
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    territory = meta["territory"]
    for repo in territory["upload_repos"]:
        repo_path = (GIT_DIR / repo["path"]).resolve()
        for item in repo.get("upload_files", []):
            if item.endswith("/*"):
                directory = repo_path / item[:-2]
                if directory.exists():
                    for path in directory.rglob("*"):
                        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                            yield path
            else:
                path = repo_path / item
                if path.exists() and path.suffix.lower() in TEXT_SUFFIXES:
                    yield path

    maintenance = territory["maintenance_only"]
    maintenance_path = (GIT_DIR / maintenance["path"]).resolve()
    for item in maintenance.get("files", []):
        path = (maintenance_path / item).resolve()
        if item.endswith("/*"):
            directory = Path(str(path)[:-2])
            if directory.exists():
                for child in directory.rglob("*"):
                    if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                        yield child
        elif path.exists() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def check_file(path):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return {"path": path, "level": "error", "message": f"UTF-8 decode failed: {exc}"}

    if path.name == "encoding_check.py":
        return None

    marker_hits = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    if marker_hits:
        return {"path": path, "level": "warning", "message": f"possible mojibake markers: {marker_hits}"}

    placeholder_hits = sum(text.count(marker) for marker in PLACEHOLDER_MARKERS)
    if placeholder_hits:
        return {"path": path, "level": "warning", "message": f"placeholder question-mark runs: {placeholder_hits}"}

    return None


def main():
    parser = argparse.ArgumentParser(description="Check UTF-8 readability and obvious mojibake markers.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when mojibake warnings are found.")
    args = parser.parse_args()

    results = []
    seen = set()
    for path in iter_declared_text_files():
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result = check_file(resolved)
        if result:
            results.append(result)

    errors = [r for r in results if r["level"] == "error"]
    warnings = [r for r in results if r["level"] == "warning"]

    print("=" * 60)
    print("  Progenitor Encoding Check")
    print("=" * 60)
    print(f"  scanned files: {len(seen)}")
    print(f"  decode errors: {len(errors)}")
    print(f"  mojibake warnings: {len(warnings)}")

    for result in results[:40]:
        rel = result["path"]
        try:
            rel = rel.relative_to(TRAE_DIR)
        except ValueError:
            pass
        print(f"  {result['level'].upper()}: {rel} - {result['message']}")

    if len(results) > 40:
        print(f"  ... {len(results) - 40} more issue(s) omitted")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
