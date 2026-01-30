#!/usr/bin/env python
"""Run benchmarks and save results to database."""

import argparse
import asyncio
import sys
import yaml
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select

from benchmark.core.config import get_settings
from benchmark.core.database import get_db_manager
from benchmark.core.models import AudioFile, Dataset, DatasetType, Result, Run, RunStatus
from benchmark.evaluation.mock_diarization import MockDiarizer
from benchmark.evaluation.metrics import DiarizationMetrics
from benchmark.utils.logging import get_logger, setup_logging

setup_logging("INFO", "text")
logger = get_logger(__name__)


def load_dataset_config(dataset_name: str) -> dict:
    """Load dataset configuration from YAML file.
    
    Args:
        dataset_name: Name of dataset (ami, sequestered, etc.)
        
    Returns:
        Dataset configuration dictionary
        
    Raises:
        ValueError: If dataset not found in config
    """
    config_path = Path("config/datasets.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Dataset config not found: {config_path}")
    
    with open(config_path) as f:
        datasets = yaml.safe_load(f)
    
    if dataset_name not in datasets:
        available = ", ".join(datasets.keys())
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Available datasets: {available}"
        )
    
    return datasets[dataset_name]


async def run_benchmark_with_save(dataset_name: str = "ami", model: str = "mock"):
    """Run benchmark and save to database."""
    settings = get_settings()

    # Initialize components
    db_manager = get_db_manager(str(settings.database_url))
    api_client = MockDiarizer(cache_dir=Path("cache"))
    metrics_calculator = DiarizationMetrics()

    logger.info("=" * 80)
    logger.info("BENCHMARK WITH DATABASE SAVE")
    logger.info("=" * 80)
    logger.info(f"Dataset: {dataset_name}")
    logger.info(f"Model: Mock Mode")

    # Load dataset config
    try:
        dataset_cfg = load_dataset_config(dataset_name)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return

    # Extract config values
    dataset_display_name = dataset_cfg["display_name"]
    benchmark_name = dataset_cfg["benchmark"]["name"]
    benchmark_description = dataset_cfg["benchmark"]["description"]
    dataset_type = DatasetType[dataset_cfg["type"].upper()]
    dataset_metadata = dataset_cfg.get("metadata", {})
    audio_dir = Path(dataset_cfg["audio_dir"])
    annotation_dir = Path(dataset_cfg["annotation_dir"])

    logger.info(f"Loaded config for dataset: {dataset_display_name}")

    # Get or create benchmark and dataset
    async with db_manager.session() as session:
        result = await session.execute(
            select(Dataset).where(Dataset.name == dataset_display_name)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            # Create benchmark first (required FK)
            from benchmark.core.models import Benchmark
            result = await session.execute(select(Benchmark).where(Benchmark.name == benchmark_name))
            benchmark = result.scalar_one_or_none()

            if not benchmark:
                benchmark = Benchmark(name=benchmark_name, description=benchmark_description)
                session.add(benchmark)
                await session.flush()

            dataset = Dataset(
                benchmark_id=benchmark.id,
                name=dataset_display_name,
                type=dataset_type,
                meta_data=dataset_metadata,
            )

            session.add(dataset)
            await session.flush()

        dataset_id = dataset.id
        await session.commit()
        logger.info(f"Using dataset: {dataset.name} (ID: {dataset_id})")

    # Create run record
    async with db_manager.session() as session:
        model_name = "Mock Mode"

        run = Run(
            dataset_id=dataset_id,
            model_name=model_name,
            config={"model": model},
            status=RunStatus.RUNNING,
            started_at=datetime.now(),
        )

        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id
        
        logger.info(f"Created Run #{run.id}")

    # Check audio directory exists
    if not audio_dir.exists():
        logger.error(f"Audio directory not found: {audio_dir}")
        logger.error(f"Please ensure {dataset_name} data is available")
        return

    ami_files = sorted([f.name for f in audio_dir.glob("*.wav")])
    logger.info(f"\nProcessing {len(ami_files)} files from {dataset_name}...")

    all_der = []
    all_jer = []

    for i, audio_file in enumerate(ami_files, 1):
        audio_path = audio_dir / audio_file
        annotation_path = annotation_dir / audio_file.replace(".wav", ".rttm")

        logger.info(f"\n[{i}/{len(ami_files)}] {audio_file}")

        try:
            # Get hypothesis from model
            hypothesis_response = await api_client.diarize(audio_path)
            
            # Convert to pyannote format
            reference = metrics_calculator.rttm_to_annotation(annotation_path)
            hypothesis = metrics_calculator.hypothesis_to_annotation(hypothesis_response)

            # Compute metrics
            der_result = metrics_calculator.compute_der(reference, hypothesis)
            jer_result = metrics_calculator.compute_jer(reference, hypothesis)

            all_der.append(der_result["DER"])
            all_jer.append(jer_result["JER"])

            logger.info(f"  DER: {der_result['DER']:.4f}, JER: {jer_result['JER']:.4f}")

            # Save results to database
            async with db_manager.session() as session:
                # Get or create audio file record
                result = await session.execute(
                    select(AudioFile).where(
                        AudioFile.dataset_id == dataset_id,
                        AudioFile.file_path == str(audio_path)
                    )
                )
                audio_file_obj = result.scalar_one_or_none()

                if not audio_file_obj:
                    audio_file_obj = AudioFile(
                        dataset_id=dataset_id,
                        file_path=str(audio_path),
                        duration=None,
                        meta_data={"filename": audio_file}
                    )
                    session.add(audio_file_obj)
                    await session.flush()

                # Save DER
                result_der = Result(
                    run_id=run_id,
                    audio_file_id=audio_file_obj.id,
                    metric_name="der",
                    value=float(der_result["DER"]),
                    details={
                        "miss": float(der_result["miss"]),
                        "false_alarm": float(der_result["false_alarm"]),
                        "confusion": float(der_result["confusion"]),
                        "total": float(der_result["total"]),
                    }
                )
                session.add(result_der)

                # Save JER
                result_jer = Result(
                    run_id=run_id,
                    audio_file_id=audio_file_obj.id,
                    metric_name="jer",
                    value=float(jer_result["JER"]),
                    details=jer_result
                )
                session.add(result_jer)

                await session.commit()

        except Exception as e:
            logger.error(f"  Error: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # Mark run as complete
    async with db_manager.session() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one()
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()
        await session.commit()

    # Print summary
    if all_der:
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Files processed: {len(all_der)}")
        logger.info(f"DER mean: {sum(all_der)/len(all_der):.4f}")
        logger.info(f"JER mean: {sum(all_jer)/len(all_jer):.4f}")
        logger.info(f"\nRun #{run_id} saved to database")
        logger.info(f"View at: http://localhost:3000/runs/{run_id}")


if __name__ == "__main__":
    # Load available datasets from config
    try:
        with open("config/datasets.yaml") as f:
            available_datasets = list(yaml.safe_load(f).keys())
    except Exception:
        available_datasets = ["ami", "sequestered"]

    parser = argparse.ArgumentParser(
        description="Run diarization benchmark and save results to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_and_save.py --dataset ami
  python run_and_save.py --dataset sequestered
  
  Add new datasets in config/datasets.yaml
        """
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="ami",
        choices=available_datasets,
        help=f"Dataset to benchmark (available: {', '.join(available_datasets)})"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mock",
        help="Model to use (default: mock). Currently only mock mode is supported."
    )

    args = parser.parse_args()

    asyncio.run(run_benchmark_with_save(
        dataset_name=args.dataset,
        model=args.model
    ))