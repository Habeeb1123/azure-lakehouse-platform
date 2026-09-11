from pathlib import Path
import argparse
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def run_step(step_name: str, command: list[str]) -> None:
    """Run one pipeline stage and stop if that stage fails."""

    print()
    print("=" * 70)
    print(f"STARTING: {step_name}")
    print("=" * 70)

    try:
        subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print()
        print("=" * 70)
        print(f"FAILED: {step_name}")
        print(f"Exit code: {exc.returncode}")
        print("=" * 70)

        raise SystemExit(exc.returncode) from exc

    print()
    print(f"COMPLETED: {step_name}")


def main() -> None:
    """Run the complete Olist medallion pipeline."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the complete Olist data pipeline from raw data "
            "through Bronze, Silver, Gold, testing and ADLS upload."
        )
    )

    parser.add_argument(
        "--storage-account",
        required=True,
        help="Azure Data Lake Storage account name.",
    )

    args = parser.parse_args()

    python = sys.executable

    pipeline_steps = [
        (
            "Bronze ingestion",
            [
                python,
                str(SRC_DIR / "ingest_olist.py"),
            ],
        ),
        (
            "Silver transformation",
            [
                python,
                str(SRC_DIR / "transform_olist_silver.py"),
            ],
        ),
        (
            "Gold analytical model",
            [
                python,
                str(SRC_DIR / "build_olist_gold.py"),
            ],
        ),
        (
            "Automated test suite",
            [
                python,
                "-m",
                "pytest",
                "-q",
            ],
        ),
        (
            "ADLS Gen2 upload",
            [
                python,
                str(SRC_DIR / "upload_to_adls.py"),
                "--storage-account",
                args.storage_account,
            ],
        ),
    ]

    print("=" * 70)
    print("OLIST END-TO-END DATA PIPELINE")
    print("=" * 70)

    for step_name, command in pipeline_steps:
        run_step(
            step_name=step_name,
            command=command,
        )

    print()
    print("=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("Bronze -> Silver -> Gold -> Tests -> ADLS Gen2")
    print("=" * 70)


if __name__ == "__main__":
    main()