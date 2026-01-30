#!/usr/bin/env python
"""Config-driven scheduler for periodic benchmark runs.

This scheduler reads dataset schedules from config/schedule.yaml and runs
benchmarks at specified intervals without requiring external dependencies.

Usage:
    python scheduler.py [--config CONFIG_FILE]
    python scheduler.py --interval HOURS  # Simple mode (single dataset)
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent / "src"))

from benchmark.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def run_benchmark(dataset: str = "ami"):
    """Run the benchmark using the run_and_save script.
    
    Args:
        dataset: Dataset name to benchmark
    """
    logger.info("=" * 80)
    logger.info(f"Starting scheduled benchmark for {dataset} at {datetime.now()}")
    logger.info("=" * 80)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "run_and_save.py", "--dataset", dataset],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Benchmark completed successfully for {dataset}")
            logger.info(result.stdout)
        else:
            logger.error(f"Benchmark failed for {dataset}")
            logger.error(result.stderr)
            
    except subprocess.TimeoutExpired:
        logger.error(f"Benchmark timed out after 1 hour for {dataset}")
    except Exception as e:
        logger.error(f"Benchmark error for {dataset}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info(f"Completed benchmark run for {dataset} at {datetime.now()}")
    logger.info("=" * 80)


async def schedule_loop(interval_hours: int, dataset: str = "ami"):
    """Run benchmarks at specified intervals (simple mode).
    
    Args:
        interval_hours: Hours between benchmark runs
        dataset: Dataset to benchmark
    """
    interval_seconds = interval_hours * 3600
    
    logger.info(f"Scheduler started - running {dataset} every {interval_hours} hours")
    logger.info(f"Next run scheduled for: {datetime.now()}")
    
    while True:
        await run_benchmark(dataset)
        
        next_run = datetime.fromtimestamp(time.time() + interval_seconds)
        logger.info(f"Next run scheduled for: {next_run}")
        
        # Wait for next interval
        await asyncio.sleep(interval_seconds)


async def dataset_schedule_loop(dataset: str, interval_hours: int, description: str = ""):
    """Run benchmarks for a specific dataset at specified intervals.
    
    Args:
        dataset: Dataset name
        interval_hours: Hours between runs
        description: Dataset description
    """
    interval_seconds = interval_hours * 3600
    
    logger.info(f"Scheduled {dataset}: every {interval_hours} hours ({interval_hours // 24} days)")
    if description:
        logger.info(f"   {description}")
    
    while True:
        await run_benchmark(dataset)
        
        next_run = datetime.fromtimestamp(time.time() + interval_seconds)
        logger.info(f"Next {dataset} run scheduled for: {next_run}")
        
        await asyncio.sleep(interval_seconds)


def load_schedule_config(config_path: Path) -> list[dict]:
    """Load schedule configuration from YAML file.
    
    Args:
        config_path: Path to schedule.yaml
        
    Returns:
        List of schedule configurations
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Schedule config not found: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    schedules = config.get("schedules", [])
    
    enabled_schedules = [s for s in schedules if s.get("enabled", True)]
    
    if not enabled_schedules:
        raise ValueError("No enabled schedules found in config")
    
    return enabled_schedules


async def run_config_driven_scheduler(config_path: Path):
    """Run scheduler based on configuration file.
    
    Args:
        config_path: Path to schedule.yaml
    """
    schedules = load_schedule_config(config_path)
    
    logger.info("=" * 80)
    logger.info("CONFIG-DRIVEN BENCHMARK SCHEDULER")
    logger.info("=" * 80)
    logger.info(f"Loaded {len(schedules)} active schedules from {config_path}")
    logger.info("")
    
    tasks = []
    for schedule in schedules:
        dataset = schedule["dataset"]
        interval_hours = schedule["interval_hours"]
        description = schedule.get("description", "")
        
        task = asyncio.create_task(
            dataset_schedule_loop(dataset, interval_hours, description)
        )
        tasks.append(task)
    
    logger.info("All schedulers started")
    logger.info("=" * 80)
    logger.info("")
    
    await asyncio.gather(*tasks)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Config-driven benchmark scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Config-driven mode (recommended)
  python scheduler.py --config config/schedule.yaml
  
  # Simple mode (single dataset)
  python scheduler.py --dataset ami --interval 168
        """
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/schedule.yaml"),
        help="Path to schedule configuration file (default: config/schedule.yaml)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Hours between runs (simple mode, requires --dataset)"
    )
    parser.add_argument(
        "--dataset",
        help="Dataset name (simple mode, requires --interval)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.log_level, "text")
    
    if args.interval or args.dataset:
        if not (args.interval and args.dataset):
            logger.error("Simple mode requires both --interval and --dataset")
            sys.exit(1)
        
        if args.interval < 1:
            logger.error("Interval must be at least 1 hour")
            sys.exit(1)
        
        logger.info("Running in simple mode (single dataset)")
        try:
            asyncio.run(schedule_loop(args.interval, args.dataset))
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            sys.exit(1)
    else:
        logger.info("Running in config-driven mode")
        try:
            asyncio.run(run_config_driven_scheduler(args.config))
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)


if __name__ == "__main__":
    main()
