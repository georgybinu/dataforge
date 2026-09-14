"""CSV ingestion utilities for the DataForge pipeline."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def ingest_csv(input_path: str, output_path: str) -> dict:
    """Read a CSV file, add ingestion metadata, and write it as Parquet.

    Args:
        input_path: Path to the source CSV file.
        output_path: Path where the Parquet output should be written.

    Returns:
        A dictionary with ingestion details and status.

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
    """
    source_path = Path(input_path)
    destination_path = Path(output_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Input CSV file not found: {input_path}")

    dataframe = pd.read_csv(source_path)
    dataframe["ingestion_timestamp"] = datetime.now(timezone.utc)
    dataframe["source_file"] = source_path.name

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(destination_path, index=False)

    return {
        "input_path": str(source_path),
        "output_path": str(destination_path),
        "records_ingested": len(dataframe),
        "status": "success",
    }
