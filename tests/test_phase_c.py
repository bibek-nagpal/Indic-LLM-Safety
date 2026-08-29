from __future__ import annotations

import sys
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

from analyze_phase_c import classify_lengths


def test_length_signal_primary_directions() -> None:
    assert classify_lengths(79, 501) == (True, False)
    assert classify_lengths(501, 79) == (False, True)
    assert classify_lengths(79, 79) == (False, False)
    assert classify_lengths(501, 501) == (False, False)


def test_length_signal_thresholds_are_strict() -> None:
    assert classify_lengths(80, 501) == (False, False)
    assert classify_lengths(79, 500) == (False, False)
    assert classify_lengths(501, 80) == (False, False)
    assert classify_lengths(500, 79) == (False, False)


def test_length_signal_custom_thresholds() -> None:
    assert classify_lengths(59, 401, short_threshold=60, long_threshold=400) == (
        True,
        False,
    )
