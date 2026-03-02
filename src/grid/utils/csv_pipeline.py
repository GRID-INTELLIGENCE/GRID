"""PEP-compliant CSV data processing pipeline.

Provides a simple parse → filter → aggregate flow for sales records.
All functions use type hints and concise docstrings to ease maintenance.
"""

from __future__ import annotations

import csv
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)

# Immutable constants for configuration
DEFAULT_MAX_WORKERS = 32
PROGRESS_CALLBACK_INTERVAL = 1000
DEFAULT_MIN_QUANTITY = 0
CSV_ENCODING = "utf-8"


@dataclass(frozen=True)
class Record:
    """A sales record with category, quantity, and price."""
    category: str
    quantity: int
    price: float

    def total_value(self) -> float:
        """Calculate total value (quantity * price)."""
        return self.quantity * self.price


@dataclass
class PipelineMetrics:
    """Comprehensive metrics for pipeline execution and discoverability."""

    # Timing metrics
    start_time: float = 0.0
    end_time: float = 0.0
    total_duration: float = 0.0

    # Processing metrics
    files_processed: int = 0
    records_processed: int = 0
    records_filtered: int = 0
    categories_found: int = 0

    # Performance metrics
    records_per_second: float = 0.0
    bytes_processed: int = 0

    # Error tracking
    errors_encountered: int = 0
    error_details: list[str] = None

    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []

    def start_tracking(self) -> None:
        """Start performance tracking."""
        self.start_time = time.perf_counter()

    def stop_tracking(self) -> None:
        """Stop performance tracking and calculate metrics."""
        self.end_time = time.perf_counter()
        self.total_duration = self.end_time - self.start_time
        if self.total_duration > 0:
            self.records_per_second = self.records_processed / self.total_duration

    def record_file_processed(self, file_path: str | Path, record_count: int) -> None:
        """Record processing of a single file."""
        self.files_processed += 1
        self.records_processed += record_count
        try:
            path = Path(file_path)
            if path.exists():
                self.bytes_processed += path.stat().st_size
        except (OSError, ValueError):
            pass  # Ignore file size errors

    def record_error(self, error_msg: str) -> None:
        """Record an error encountered during processing."""
        self.errors_encountered += 1
        self.error_details.append(error_msg)

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive processing summary."""
        return {
            "duration_seconds": round(self.total_duration, 2),
            "files_processed": self.files_processed,
            "records_processed": self.records_processed,
            "records_filtered": self.records_filtered,
            "categories_found": self.categories_found,
            "records_per_second": round(self.records_per_second, 1),
            "bytes_processed": self.bytes_processed,
            "errors_encountered": self.errors_encountered,
            "error_details": self.error_details[:10],  # Limit error details
        }


Records = list[Record]


def parse_csv(file_path: str | Path) -> Records:
    """Read a CSV file and return typed sales records.

    For memory efficiency with large files, consider using parse_csv_streaming().

    Each row must contain ``category``, ``quantity``, and ``price`` fields.
    Quantity is converted to ``int`` and price to ``float`` for computation.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required fields are missing or data cannot be converted.
    """
    return list(parse_csv_streaming(file_path))


def parse_csv_streaming(file_path: str | Path) -> Iterable[Record]:
    """Stream CSV records as a generator for memory-efficient processing.

    Yields Record objects one by one, suitable for large files.

    Each row must contain ``category``, ``quantity``, and ``price`` fields.
    Quantity is converted to ``int`` and price to ``float`` for computation.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required fields are missing or data cannot be converted.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open(newline="", encoding=CSV_ENCODING) as csvfile:
        reader = csv.DictReader(csvfile)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
            try:
                record = Record(
                    category=row["category"].strip(),
                    quantity=int(row["quantity"]),
                    price=float(row["price"]),
                )
                if record.quantity < 0 or record.price < 0:
                    raise ValueError(f"Negative values not allowed at row {row_num}")
                yield record
            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(f"Invalid data at row {row_num}: {e}") from e


def filter_records(records: Records, min_quantity: int) -> Records:
    """Filter out records whose quantity is below ``min_quantity``."""
    return [rec for rec in records if rec.quantity >= min_quantity]


def filter_records_streaming(records: Iterable[Record], min_quantity: int) -> Iterable[Record]:
    """Stream filter records whose quantity is below ``min_quantity``.

    Yields filtered Record objects one by one for memory efficiency.
    """
    for rec in records:
        if rec.quantity >= min_quantity:
            yield rec


def aggregate_sales(records: Iterable[Record]) -> dict[str, float]:
    """Aggregate total sales (quantity × price) by category.

    Uses a generator approach for memory efficiency with large datasets.
    """
    totals: dict[str, float] = {}
    for rec in records:
        category = rec.category
        sales = rec.total_value()
        totals[category] = totals.get(category, 0.0) + sales
    return totals


def aggregate_sales_with_progress(records: Iterable[Record], progress_callback: Callable[[int, Record], None] | None = None) -> dict[str, float]:
    """Aggregate total sales with optional progress tracking.

    Args:
        records: Iterable of Record objects
        progress_callback: Optional callback function called for each record
                          with (record_index, record) arguments

    Returns:
        Dictionary of category totals
    """
    totals: dict[str, float] = {}
    for idx, rec in enumerate(records):
        if progress_callback:
            progress_callback(idx, rec)

        category = rec.category
        sales = rec.total_value()
        totals[category] = totals.get(category, 0.0) + sales
    return totals


import argparse
import sys


def process_multiple_csvs(
    file_paths: list[str | Path],
    min_quantity: int = DEFAULT_MIN_QUANTITY,
    max_workers: int | None = None
) -> dict[str, float]:
    """
    Process multiple CSV files concurrently and aggregate sales.

    Uses ThreadPoolExecutor for concurrent file I/O, suitable for I/O bound tasks.
    Follows Python threading documentation recommendations for concurrent file operations.

    Args:
        file_paths: List of CSV file paths to process
        min_quantity: Minimum quantity filter to apply
        max_workers: Maximum worker threads (default: min(32, len(file_paths)))

    Returns:
        Aggregated sales totals by category

    Raises:
        FileNotFoundError: If any file does not exist
        ValueError: If any file contains invalid data
    """
    if max_workers is None:
        max_workers = min(DEFAULT_MAX_WORKERS, len(file_paths))

    all_records: Records = []

    # Use ThreadPoolExecutor for concurrent file reading (I/O bound)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all file parsing tasks
        future_to_path = {
            executor.submit(parse_csv, path): path
            for path in file_paths
        }

        # Collect results as they complete
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                records = future.result()
                all_records.extend(records)
                logger.info(f"Processed {len(records)} records from {path}")
            except Exception as exc:
                logger.error(f"Failed to process {path}: {exc}")
                raise

    # Apply filtering if requested
    if min_quantity > 0:
        all_records = filter_records(all_records, min_quantity)
        logger.info(f"Filtered to {len(all_records)} records total")

    # Aggregate all results
    totals = aggregate_sales(all_records)
    logger.info(f"Aggregated sales across {len(file_paths)} files")

    return totals


def process_streaming_pipeline(
    file_paths: list[str | Path],
    min_quantity: int = DEFAULT_MIN_QUANTITY,
    max_workers: int | None = None,
    progress_callback: Callable[[str, PipelineMetrics], None] | None = None,
    enable_metrics: bool = True
) -> tuple[dict[str, float], PipelineMetrics | None]:
    """
    Process CSV files with full streaming and discoverability features.

    This function provides the most advanced processing capabilities:
    - True streaming with generators (memory efficient)
    - Concurrent file processing with ThreadPoolExecutor
    - Comprehensive progress tracking and metrics
    - Full error handling and reporting

    Args:
        file_paths: List of CSV file paths to process
        min_quantity: Minimum quantity filter to apply
        max_workers: Maximum worker threads
        progress_callback: Optional callback for progress updates
        enable_metrics: Whether to track detailed metrics

    Returns:
        Tuple of (aggregated_totals, metrics) where metrics is None if disabled
    """
    metrics = PipelineMetrics() if enable_metrics else None

    if metrics:
        metrics.start_tracking()
        logger.info(f"Starting streaming pipeline with {len(file_paths)} files")

    if max_workers is None:
        max_workers = min(DEFAULT_MAX_WORKERS, len(file_paths))

    # Use streaming processing for memory efficiency
    all_records: list[Record] = []

    def progress_collector(file_path: str | Path, record_count: int) -> None:
        """Collect progress information."""
        if metrics:
            metrics.record_file_processed(file_path, record_count)
        if progress_callback and metrics:
            progress_callback("file_processed", metrics)

    # Process files concurrently with streaming
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit streaming parsing tasks
        future_to_path = {}
        for path in file_paths:
            future = executor.submit(_process_single_file_streaming, path, min_quantity, progress_collector)
            future_to_path[future] = path

        # Collect streaming results as they complete
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                file_records = future.result()
                all_records.extend(file_records)
                logger.debug(f"Collected {len(file_records)} filtered records from {path}")
            except Exception as exc:
                error_msg = f"Failed to process {path}: {exc}"
                logger.error(error_msg)
                if metrics:
                    metrics.record_error(error_msg)
                raise

    # Aggregate with progress tracking
    def record_progress(idx: int, rec: Record) -> None:
        """Record aggregation progress."""
        if idx % PROGRESS_CALLBACK_INTERVAL == 0 and progress_callback and metrics:  # Progress every N records
            progress_callback("aggregation_progress", metrics)

    totals = aggregate_sales_with_progress(all_records, record_progress if progress_callback else None)

    # Final metrics update
    if metrics:
        metrics.categories_found = len(totals)
        metrics.records_filtered = len(all_records)
        metrics.stop_tracking()

        logger.info(f"Pipeline completed: {metrics.get_summary()}")

        if progress_callback:
            progress_callback("completed", metrics)

    return totals, metrics


def _process_single_file_streaming(
    file_path: str | Path,
    min_quantity: int,
    progress_callback: Callable[[str | Path, int], None]
) -> list[Record]:
    """Process a single file with streaming and return filtered records."""
    try:
        # Stream parse the file
        records_iter = parse_csv_streaming(file_path)

        # Stream filter if needed
        if min_quantity > 0:
            records_iter = filter_records_streaming(records_iter, min_quantity)

        # Collect filtered records (still need to materialize for ThreadPoolExecutor)
        # In a more advanced implementation, this could return a generator
        # But ThreadPoolExecutor requires serializable results
        filtered_records = list(records_iter)

        # Report progress
        progress_callback(file_path, len(filtered_records))

        return filtered_records

    except Exception as e:
        # Re-raise with file context
        raise RuntimeError(f"Error processing {file_path}: {e}") from e


def run_pipeline(file_path: str, min_quantity: int = DEFAULT_MIN_QUANTITY, output_file: str | None = None) -> None:
    """Run the complete CSV processing pipeline."""
    try:
        logger.info(f"Processing CSV file: {file_path}")
        records = parse_csv(file_path)
        logger.info(f"Parsed {len(records)} records")

        if min_quantity > 0:
            records = filter_records(records, min_quantity)
            logger.info(f"Filtered to {len(records)} records (min_quantity={min_quantity})")

        totals = aggregate_sales(records)

        if output_file:
            write_results(totals, output_file)
            logger.info(f"Results written to {output_file}")
        else:
            print_results(totals)

    except (FileNotFoundError, ValueError, OSError, UnicodeDecodeError) as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def print_results(totals: dict[str, float]) -> None:
    """Print aggregated results to stdout."""
    for category, total in sorted(totals.items()):
        print(f"{category}: {total:.2f}")


def write_results(totals: dict[str, float], output_file: str) -> None:
    """Write aggregated results to a file."""
    path = Path(output_file)
    with path.open("w", encoding=CSV_ENCODING) as f:
        for category, total in sorted(totals.items()):
            f.write(f"{category}: {total:.2f}\n")


def main() -> None:
    """Command-line interface for the CSV pipeline."""
    parser = argparse.ArgumentParser(
        description="Process CSV sales data: parse, filter, and aggregate by category."
    )
    parser.add_argument("file", help="Path to CSV file")
    parser.add_argument(
        "--min-quantity", type=int, default=DEFAULT_MIN_QUANTITY,
        help="Minimum quantity to include in results (default: 0)"
    )
    parser.add_argument(
        "--output", "-o", help="Output file for results (default: stdout)"
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO", help="Set logging level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s"
    )

    run_pipeline(args.file, args.min_quantity, args.output)


if __name__ == "__main__":
    main()
