"""Unit tests for database models."""

from datetime import datetime

import pytest
from sqlalchemy import select

from benchmark.core.models import AudioFile, Benchmark, Dataset, Result, Run, RunStatus


@pytest.mark.asyncio
async def test_create_benchmark(db_session):
    """Test creating a benchmark."""
    benchmark = Benchmark(
        name="Test Benchmark",
        description="Test description",
    )
    db_session.add(benchmark)
    await db_session.commit()

    assert benchmark.id is not None
    assert benchmark.name == "Test Benchmark"
    assert benchmark.created_at is not None


@pytest.mark.asyncio
async def test_create_dataset(db_session):
    """Test creating a dataset."""
    # Create benchmark first
    benchmark = Benchmark(name="Test Benchmark")
    db_session.add(benchmark)
    await db_session.flush()

    # Create dataset
    dataset = Dataset(
        benchmark_id=benchmark.id,
        name="Test Dataset",
        type="ami",
        metadata={"split": "test"},
    )
    db_session.add(dataset)
    await db_session.commit()

    assert dataset.id is not None
    assert dataset.benchmark_id == benchmark.id


@pytest.mark.asyncio
async def test_create_run(db_session):
    """Test creating a run."""
    # Create benchmark and dataset
    benchmark = Benchmark(name="Test Benchmark")
    db_session.add(benchmark)
    await db_session.flush()

    dataset = Dataset(
        benchmark_id=benchmark.id,
        name="Test Dataset",
        type="ami",
    )
    db_session.add(dataset)
    await db_session.flush()

    # Create run
    run = Run(
        dataset_id=dataset.id,
        model_name="test-model",
        status=RunStatus.PENDING.value,
        config={"min_speakers": 2},
    )
    db_session.add(run)
    await db_session.commit()

    assert run.id is not None
    assert run.dataset_id == dataset.id
    assert run.status == RunStatus.PENDING.value


@pytest.mark.asyncio
async def test_create_result(db_session):
    """Test creating a result."""
    # Create necessary parent objects
    benchmark = Benchmark(name="Test Benchmark")
    db_session.add(benchmark)
    await db_session.flush()

    dataset = Dataset(benchmark_id=benchmark.id, name="Test Dataset", type="ami")
    db_session.add(dataset)
    await db_session.flush()

    run = Run(dataset_id=dataset.id, model_name="test-model")
    db_session.add(run)
    await db_session.flush()

    # Create result
    result = Result(
        run_id=run.id,
        metric_name="DER",
        value=0.15,
        details={"miss": 0.05, "false_alarm": 0.05, "confusion": 0.05},
    )
    db_session.add(result)
    await db_session.commit()

    assert result.id is not None
    assert result.run_id == run.id
    assert result.value == 0.15


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test cascade deletion of related objects."""
    # Create benchmark with dataset
    benchmark = Benchmark(name="Test Benchmark")
    db_session.add(benchmark)
    await db_session.flush()

    dataset = Dataset(benchmark_id=benchmark.id, name="Test Dataset", type="ami")
    db_session.add(dataset)
    await db_session.commit()

    dataset_id = dataset.id

    # Delete benchmark
    await db_session.delete(benchmark)
    await db_session.commit()

    # Verify dataset was also deleted
    result = await db_session.execute(select(Dataset).where(Dataset.id == dataset_id))
    assert result.scalar_one_or_none() is None
