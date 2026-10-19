import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PipelineStage:
    name: str
    module: str


PIPELINE_STAGES = [
    PipelineStage(
        "Generate customers",
        "src.generate_customers",
    ),
    PipelineStage(
        "Generate accounts",
        "src.generate_accounts",
    ),
    PipelineStage(
        "Generate transactions",
        "src.generate_transactions",
    ),
    PipelineStage(
        "Generate loans",
        "src.generate_loans",
    ),
    PipelineStage(
        "Validate customers",
        "src.validate_customers",
    ),
    PipelineStage(
        "Validate accounts",
        "src.validate_accounts",
    ),
    PipelineStage(
        "Validate transactions",
        "src.validate_transactions",
    ),
    PipelineStage(
        "Validate loans",
        "src.validate_loans",
    ),
    PipelineStage(
        "Build Pandas customer metrics",
        "src.build_customer_metrics",
    ),
    PipelineStage(
        "Load PostgreSQL warehouse",
        "src.load_postgres",
    ),
    PipelineStage(
        "Reconcile Pandas and SQL metrics",
        "src.reconcile_customer_metrics",
    ),
    PipelineStage(
        "Build PySpark customer metrics",
        "src.build_customer_metrics_spark",
    ),
    PipelineStage(
        "Reconcile Pandas, Spark and SQL metrics",
        "src.reconcile_customer_metrics_spark",
    ),
]


def validate_environment():
    if not os.getenv("DB_PASSWORD"):
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )


def run_stage(
    stage_number,
    total_stages,
    stage,
):
    print()
    print("=" * 72)
    print(
        f"[{stage_number}/{total_stages}] "
        f"{stage.name}"
    )
    print("=" * 72)

    started_at = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            stage.module,
        ],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )

    elapsed = time.perf_counter() - started_at

    if result.returncode != 0:
        print()
        print(
            f"FAILED: {stage.name} "
            f"({elapsed:.2f}s)"
        )

        raise RuntimeError(
            f"Pipeline stopped because "
            f"'{stage.name}' failed with "
            f"exit code {result.returncode}."
        )

    print()
    print(
        f"PASSED: {stage.name} "
        f"({elapsed:.2f}s)"
    )

    return elapsed


def run_tests():
    print()
    print("=" * 72)
    print("Running automated test suite")
    print("=" * 72)

    started_at = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )

    elapsed = time.perf_counter() - started_at

    if result.returncode != 0:
        print()
        print(
            f"FAILED: Automated tests "
            f"({elapsed:.2f}s)"
        )

        raise RuntimeError(
            "Pipeline stopped because "
            "the automated test suite failed."
        )

    print()
    print(
        f"PASSED: Automated tests "
        f"({elapsed:.2f}s)"
    )

    return elapsed


def main():
    print()
    print(
        "Financial Customer Intelligence Pipeline"
    )
    print(
        "=" * 40
    )

    validate_environment()

    pipeline_started_at = time.perf_counter()

    completed_stages = []

    try:
        total_stages = len(
            PIPELINE_STAGES
        )

        for index, stage in enumerate(
            PIPELINE_STAGES,
            start=1,
        ):
            elapsed = run_stage(
                index,
                total_stages,
                stage,
            )

            completed_stages.append(
                (
                    stage.name,
                    elapsed,
                )
            )

        test_elapsed = run_tests()

        completed_stages.append(
            (
                "Automated tests",
                test_elapsed,
            )
        )

    except Exception as exc:
        total_elapsed = (
            time.perf_counter()
            - pipeline_started_at
        )

        print()
        print("=" * 72)
        print("PIPELINE FAILED")
        print("=" * 72)
        print(str(exc))
        print(
            f"Elapsed time: "
            f"{total_elapsed:.2f}s"
        )

        raise SystemExit(1) from exc

    total_elapsed = (
        time.perf_counter()
        - pipeline_started_at
    )

    print()
    print("=" * 72)
    print("PIPELINE SUMMARY")
    print("=" * 72)

    for name, elapsed in completed_stages:
        print(
            f"PASS  {name:<45} "
            f"{elapsed:>7.2f}s"
        )

    print("-" * 72)
    print(
        f"Pipeline completed successfully "
        f"in {total_elapsed:.2f}s."
    )


if __name__ == "__main__":
    main()