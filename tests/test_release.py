from __future__ import annotations

from pathlib import Path

from src.release import read_version, release_readiness_report, release_ready


def test_release_readiness_passes_for_repository() -> None:
    report = release_readiness_report()
    assert set(report["status"]) == {"pass"}
    assert release_ready()


def test_read_version_defaults_when_missing(tmp_path: Path) -> None:
    assert read_version(tmp_path) == "0.0.0"


def test_release_report_fails_missing_files(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("data/*.db\n", encoding="utf-8")
    report = release_readiness_report(tmp_path)
    assert "fail" in report["status"].tolist()
