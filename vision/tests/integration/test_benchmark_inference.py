from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/scripts"))

from benchmark_inference import summarize_ms  # noqa: E402


def test_summarize_ms_reports_stable_percentiles() -> None:
    summary = summarize_ms([1.0, 2.0, 3.0, 4.0])
    assert summary["mean"] == pytest.approx(2.5)
    assert summary["p50"] == pytest.approx(2.5)
    assert summary["p95"] == pytest.approx(3.85)


def test_summarize_ms_rejects_empty_or_nonfinite_samples() -> None:
    with pytest.raises(ValueError, match="non-empty finite"):
        summarize_ms([])
    with pytest.raises(ValueError, match="non-empty finite"):
        summarize_ms([1.0, float("nan")])
