from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))
sys.path.insert(0, str(ROOT / "vision/scripts"))

from evaluate_templates import evaluate_leave_one_clip_out  # noqa: E402
from signrec.recognizer import ClipTemplate  # noqa: E402


def test_leave_one_out_evaluates_only_repeated_classes() -> None:
    templates = [
        ClipTemplate("你好", np.asarray([[1.0, 0.0]], dtype=np.float32)),
        ClipTemplate("你好", np.asarray([[1.0, 0.0]], dtype=np.float32)),
        ClipTemplate("谢谢", np.asarray([[0.0, 1.0]], dtype=np.float32)),
    ]

    result = evaluate_leave_one_clip_out(templates)

    assert result.total_templates == 3
    assert result.evaluated_clips == 2
    assert result.evaluated_classes == 1
    assert result.top1_accuracy == pytest.approx(1.0)
    assert result.macro_f1 == pytest.approx(1.0)
    assert result.singleton_distractor_rate == pytest.approx(0.0)
    threshold = result.thresholds[0]
    assert threshold.known_coverage == pytest.approx(1.0)
    assert threshold.accepted_known_accuracy == pytest.approx(1.0)
    assert threshold.singleton_false_accept_rate == pytest.approx(0.0)


def test_leave_one_out_requires_repeated_class() -> None:
    templates = [ClipTemplate("你好", np.asarray([[1.0, 0.0]], dtype=np.float32))]
    with pytest.raises(ValueError, match="2 or more"):
        evaluate_leave_one_clip_out(templates)
