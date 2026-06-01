from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = PROJECT_ROOT / "VERSION"

REQUIRED_RELEASE_FILES = [
    "VERSION",
    "CHANGELOG.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/screenshots/README.md",
    "sample_data/watchlist_sample.csv",
    "sample_data/trades_sample.csv",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)TUSHARE_TOKEN\s*=\s*['\"][^'\"]{8,}['\"]"),
]

SCAN_SUFFIXES = {".py", ".md", ".toml", ".txt", ".csv", ".yml", ".yaml"}


def read_version(root: Path | None = None) -> str:
    base = root or PROJECT_ROOT
    path = base / "VERSION"
    if not path.exists():
        return "0.0.0"
    return path.read_text(encoding="utf-8").strip() or "0.0.0"


def release_readiness_report(root: Path | None = None) -> pd.DataFrame:
    base = root or PROJECT_ROOT
    rows = [
        _required_files_check(base),
        _gitignore_database_check(base),
        _sample_data_check(base),
        _secret_scan_check(base),
        _readme_release_check(base),
    ]
    return pd.DataFrame(rows)


def release_ready(root: Path | None = None) -> bool:
    report = release_readiness_report(root)
    return bool((report["status"] == "pass").all())


def _required_files_check(root: Path) -> dict:
    missing = [path for path in REQUIRED_RELEASE_FILES if not (root / path).exists()]
    return {
        "check": "release files",
        "status": "pass" if not missing else "fail",
        "detail": "all release files exist" if not missing else "missing: " + ", ".join(missing),
    }


def _gitignore_database_check(root: Path) -> dict:
    gitignore = root / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    ok = "data/*.db" in text
    return {
        "check": "database ignore",
        "status": "pass" if ok else "fail",
        "detail": "data/*.db is ignored" if ok else "data/*.db is not ignored",
    }


def _sample_data_check(root: Path) -> dict:
    watchlist = root / "sample_data" / "watchlist_sample.csv"
    trades = root / "sample_data" / "trades_sample.csv"
    ok = (
        watchlist.exists()
        and trades.exists()
        and watchlist.stat().st_size > 0
        and trades.stat().st_size > 0
    )
    return {
        "check": "sample data",
        "status": "pass" if ok else "fail",
        "detail": "sample CSV files are present" if ok else "sample CSV files are missing or empty",
    }


def _secret_scan_check(root: Path) -> dict:
    hits: list[str] = []
    for path in _iter_scannable_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            hits.append(str(path.relative_to(root)))
    return {
        "check": "secret scan",
        "status": "pass" if not hits else "fail",
        "detail": (
            "no obvious committed secrets" if not hits else "possible secrets: " + ", ".join(hits)
        ),
    }


def _readme_release_check(root: Path) -> dict:
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    ok = "PHASE_10" in text and "stable release" in text.lower()
    return {
        "check": "README release status",
        "status": "pass" if ok else "fail",
        "detail": (
            "README mentions stable release status"
            if ok
            else "README release status is incomplete"
        ),
    }


def _iter_scannable_files(root: Path):
    ignored_parts = {".git", ".pytest_cache", ".ruff_cache", "__pycache__", "data"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        yield path
