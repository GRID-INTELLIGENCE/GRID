"""Tests for the PEP-compliant CSV data pipeline."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import pytest

from grid.utils.csv_pipeline import (
    Record,
    aggregate_sales,
    filter_records,
    parse_csv,
    print_results,
    run_pipeline,
    write_results,
)


def _write_csv(tmp_path: Path, rows: Iterable[dict[str, str]]) -> Path:
    path = tmp_path / "data.csv"
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["category", "quantity", "price"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_parse_csv_reads_and_converts_types(tmp_path: Path):
    rows = [
        {"category": "books", "quantity": "2", "price": "10.5"},
        {"category": "games", "quantity": "3", "price": "20.0"},
    ]
    file_path = _write_csv(tmp_path, rows)

    records = parse_csv(file_path)

    assert len(records) == 2
    assert records[0].category == "books"
    assert records[0].quantity == 2
    assert records[0].price == 10.5


def test_filter_records_applies_min_quantity():
    records = [
        Record("books", 2, 10.0),
        Record("games", 5, 20.0),
    ]

    filtered = filter_records(records, min_quantity=3)

    assert len(filtered) == 1
    assert filtered[0].category == "games"


def test_aggregate_sales_sums_by_category():
    records = [
        Record("books", 2, 10.0),
        Record("books", 1, 15.0),
        Record("games", 3, 20.0),
    ]

    totals = aggregate_sales(records)

    assert totals["books"] == pytest.approx(35.0)
    assert totals["games"] == pytest.approx(60.0)


def test_parse_csv_handles_empty_file(tmp_path: Path):
    file_path = _write_csv(tmp_path, [])

    records = parse_csv(file_path)

    assert records == []


def test_aggregate_sales_handles_multiple_categories():
    records = [
        Record("books", 1, 10.0),
        Record("books", 3, 5.0),
        Record("music", 2, 12.5),
    ]

    totals = aggregate_sales(records)

    assert totals["books"] == pytest.approx(25.0)
    assert totals["music"] == pytest.approx(25.0)


def test_parse_csv_raises_file_not_found(tmp_path: Path):
    non_existent = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        parse_csv(non_existent)


def test_parse_csv_raises_value_error_missing_fields(tmp_path: Path):
    # CSV with missing 'price' field
    rows = [{"category": "books", "quantity": "2"}]  # no price
    file_path = _write_csv(tmp_path, rows)

    with pytest.raises(ValueError, match="Invalid data at row 2"):
        parse_csv(file_path)


def test_parse_csv_raises_value_error_invalid_quantity(tmp_path: Path):
    rows = [{"category": "books", "quantity": "not_a_number", "price": "10.5"}]
    file_path = _write_csv(tmp_path, rows)

    with pytest.raises(ValueError, match="Invalid data at row 2"):
        parse_csv(file_path)


def test_parse_csv_raises_value_error_negative_quantity(tmp_path: Path):
    rows = [{"category": "books", "quantity": "-1", "price": "10.5"}]
    file_path = _write_csv(tmp_path, rows)

    with pytest.raises(ValueError, match="Negative values not allowed"):
        parse_csv(file_path)


def test_parse_csv_raises_value_error_negative_price(tmp_path: Path):
    rows = [{"category": "books", "quantity": "2", "price": "-10.5"}]
    file_path = _write_csv(tmp_path, rows)

    with pytest.raises(ValueError, match="Negative values not allowed"):
        parse_csv(file_path)


def test_run_pipeline_success(tmp_path: Path, caplog, capsys):
    rows = [
        {"category": "books", "quantity": "2", "price": "10.5"},
        {"category": "games", "quantity": "3", "price": "20.0"},
    ]
    file_path = _write_csv(tmp_path, rows)

    with caplog.at_level("INFO"):
        run_pipeline(str(file_path))

    assert "Processing CSV file" in caplog.text
    assert "Parsed 2 records" in caplog.text

    captured = capsys.readouterr()
    assert "books: 21.00" in captured.out
    assert "games: 60.00" in captured.out


def test_run_pipeline_with_filter(tmp_path: Path, caplog, capsys):
    rows = [
        {"category": "books", "quantity": "1", "price": "10.0"},  # below min
        {"category": "games", "quantity": "3", "price": "20.0"},  # above min
    ]
    file_path = _write_csv(tmp_path, rows)

    with caplog.at_level("INFO"):
        run_pipeline(str(file_path), min_quantity=2)

    assert "Filtered to 1 records" in caplog.text

    captured = capsys.readouterr()
    assert "games: 60.00" in captured.out
    assert "books" not in captured.out  # should be filtered out


def test_run_pipeline_with_output_file(tmp_path: Path, caplog):
    rows = [{"category": "books", "quantity": "2", "price": "10.0"}]
    file_path = _write_csv(tmp_path, rows)
    output_file = tmp_path / "output.txt"

    with caplog.at_level("INFO"):
        run_pipeline(str(file_path), output_file=str(output_file))

    assert "Results written to" in caplog.text
    content = output_file.read_text()
    assert "books: 20.00" in content


def test_run_pipeline_file_not_found_error(tmp_path: Path, caplog):
    non_existent = tmp_path / "missing.csv"

    with pytest.raises(SystemExit):
        run_pipeline(str(non_existent))

    assert "Pipeline error: CSV file not found" in caplog.text


def test_print_results(capsys):
    totals = {"books": 35.0, "games": 60.0}

    print_results(totals)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert "books: 35.00" in lines
    assert "games: 60.00" in lines


def test_write_results(tmp_path: Path):
    totals = {"books": 25.0, "music": 37.5}
    output_file = tmp_path / "results.txt"

    write_results(totals, str(output_file))

    content = output_file.read_text()
    lines = content.strip().split("\n")
    assert "books: 25.00" in lines
    assert "music: 37.50" in lines
