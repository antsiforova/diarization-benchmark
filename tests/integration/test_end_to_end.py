"""End-to-end integration tests."""

from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_setup_workflow(db_session, test_settings):
    """Test database setup workflow."""
    from benchmark.core.database import DatabaseManager

    db_manager = DatabaseManager(str(test_settings.database_url))

    # Should be able to create tables
    await db_manager.create_tables()

    # Should be able to create session
    async with db_manager.session() as session:
        assert session is not None

    await db_manager.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ami_dataset_registration(db_session, tmp_path):
    """Test AMI dataset registration flow."""
    from benchmark.core.models import AudioFile, Benchmark, Dataset

    # Create benchmark
    benchmark = Benchmark(
        name="Test AMI",
        description="Test benchmark",
    )
    db_session.add(benchmark)
    await db_session.flush()

    # Create dataset
    dataset = Dataset(
        benchmark_id=benchmark.id,
        name="AMI Test",
        type="ami",
        metadata={"split": "test"},
    )
    db_session.add(dataset)
    await db_session.flush()

    # Add audio file
    audio_file = AudioFile(
        dataset_id=dataset.id,
        file_path=str(tmp_path / "test.wav"),
        metadata={"file_id": "test1"},
    )
    db_session.add(audio_file)
    await db_session.commit()

    # Verify
    assert benchmark.id is not None
    assert dataset.id is not None
    assert audio_file.id is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_evaluation_result_storage(db_session):
    """Test storing evaluation results."""
    from benchmark.core.models import Benchmark, Dataset, Result, Run

    # Create test data
    benchmark = Benchmark(name="Test")
    db_session.add(benchmark)
    await db_session.flush()

    dataset = Dataset(benchmark_id=benchmark.id, name="Test Dataset", type="ami")
    db_session.add(dataset)
    await db_session.flush()

    run = Run(
        dataset_id=dataset.id,
        model_name="test-model",
        status="completed",
    )
    db_session.add(run)
    await db_session.flush()

    # Store results
    metrics = {
        "DER": 0.15,
        "JER": 0.20,
        "DER_mean": 0.15,
        "DER_std": 0.02,
    }

    for metric_name, value in metrics.items():
        result = Result(
            run_id=run.id,
            metric_name=metric_name,
            value=value,
        )
        db_session.add(result)

    await db_session.commit()

    # Verify
    from sqlalchemy import select

    result = await db_session.execute(select(Result).where(Result.run_id == run.id))
    results = result.scalars().all()

    assert len(results) == len(metrics)
    assert all(r.run_id == run.id for r in results)


@pytest.mark.integration
def test_cli_available():
    """Test CLI is available and responds."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "benchmark.cli", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Diarization Benchmark CLI" in result.stdout
