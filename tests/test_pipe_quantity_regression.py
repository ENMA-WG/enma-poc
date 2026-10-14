import csv
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETAIL_FILE = PROJECT_ROOT / "output" / "pipes_detail.csv"
SUMMARY_FILE = PROJECT_ROOT / "output" / "pipes_summary.csv"


def read_csv(path):
    assert path.exists(), f"Regression test file not found: {path}"

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        return list(csv.DictReader(f))


def get_length(row):
    """
    Return pipe length from the ENMA summary CSV.
    """
    value = row.get("長さ_m")

    if value in ("", None):
        raise AssertionError(
            f"長さ_m is missing or blank: {row}"
        )

    return float(value)


def test_pipe_detail_row_count():
    """All known pipe segments must be extracted."""
    rows = read_csv(DETAIL_FILE)

    assert len(rows) == 252


def test_pipe_summary_row_count():
    """Known aggregation result must remain unchanged."""
    rows = read_csv(SUMMARY_FILE)

    assert len(rows) == 138


def test_pipe_total_length():
    """Total pipe length must match the validated baseline."""
    rows = read_csv(SUMMARY_FILE)

    total_length = sum(get_length(row) for row in rows)

    assert total_length == pytest.approx(
        649.090,
        abs=0.001,
    )


def test_pipe_length_by_direction():
    """Pipe lengths by direction must match the validated baseline."""
    rows = read_csv(SUMMARY_FILE)

    lengths = {}

    for direction in ("水平管", "立管", "勾配管"):
        lengths[direction] = sum(
            get_length(row)
            for row in rows
            if row.get("方向区分") == direction
        )

    assert lengths["水平管"] == pytest.approx(
        375.963,
        abs=0.001,
    )

    assert lengths["立管"] == pytest.approx(
        273.127,
        abs=0.001,
    )

    assert lengths["勾配管"] == pytest.approx(
        0.000,
        abs=0.001,
    )
