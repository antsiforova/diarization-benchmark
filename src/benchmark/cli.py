"""Command-line interface for benchmark system."""

import asyncio
from pathlib import Path

import typer

from benchmark.core.config import get_settings
from benchmark.core.database import get_db_manager
from benchmark.utils.logging import get_logger, setup_logging

app = typer.Typer(help="Diarization Benchmark CLI")
logger = get_logger(__name__)


from dotenv import load_dotenv

load_dotenv()


@app.command()
def setup() -> None:
    """Setup the benchmark system (database, directories, etc.)."""
    typer.echo("Setting up benchmark system...")

    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    settings.ensure_directories()
    typer.echo(f"Created directories: {settings.data_dir}, {settings.results_dir}, {settings.cache_dir}")

    async def _setup_db() -> None:
        db_manager = get_db_manager(str(settings.database_url))
        await db_manager.create_tables()
        typer.echo("Database tables created")

    asyncio.run(_setup_db())
    typer.echo("Setup complete")




@app.command()
def export_results(
    run_id: int,
    output: Path = typer.Option(default="results.json", help="Output file path"),
    format: str = typer.Option(default="json", help="Output format (json, csv)"),
) -> None:
    """Export benchmark results."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    typer.echo(f"Exporting results for run {run_id}...")

    async def _export() -> None:
        from sqlalchemy import select

        from benchmark.core.models import Result, Run

        db_manager = get_db_manager(str(settings.database_url))

        async with db_manager.session() as session:
            # Get run
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()

            if not run:
                typer.echo(f"Run {run_id} not found", err=True)
                raise typer.Exit(1)

            # Get results
            result = await session.execute(
                select(Result).where(Result.run_id == run_id)
            )
            results = result.scalars().all()

            # Export
            if format == "json":
                import json

                data = {
                    "run": {
                        "id": run.id,
                        "model": run.model_name,
                        "dataset_id": run.dataset_id,
                        "status": run.status,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    },
                    "results": [
                        {
                            "metric_name": r.metric_name,
                            "value": r.value,
                            "audio_file_id": r.audio_file_id,
                        }
                        for r in results
                    ],
                }

                with open(output, "w") as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                import csv

                with open(output, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["metric_name", "value", "audio_file_id"])
                    for r in results:
                        writer.writerow([r.metric_name, r.value, r.audio_file_id])

            typer.echo(f"Results exported to {output}")

    asyncio.run(_export())


@app.command()
def list_runs(
    limit: int = typer.Option(default=10, help="Number of runs to show"),
) -> None:
    """List recent benchmark runs."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    async def _list() -> None:
        from sqlalchemy import select

        from benchmark.core.models import Run

        db_manager = get_db_manager(str(settings.database_url))

        async with db_manager.session() as session:
            result = await session.execute(
                select(Run).order_by(Run.created_at.desc()).limit(limit)
            )
            runs = result.scalars().all()

            if not runs:
                typer.echo("No runs found")
                return

            typer.echo("\nRecent Runs:")
            typer.echo("=" * 80)
            for run in runs:
                typer.echo(
                    f"Run {run.id}: {run.model_name} "
                    f"(Dataset {run.dataset_id}) - {run.status}"
                )
                if run.started_at:
                    typer.echo(f"   Started: {run.started_at}")
                if run.completed_at:
                    duration = (run.completed_at - run.started_at).total_seconds()
                    typer.echo(f"   Duration: {duration:.1f}s")

    asyncio.run(_list())


@app.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()

    typer.echo("\nConfiguration:")
    typer.echo("=" * 80)
    typer.echo(f"Environment: {settings.environment}")
    typer.echo(f"Database: {settings.database_url}")
    typer.echo(f"Data directory: {settings.data_dir}")
    typer.echo(f"Results directory: {settings.results_dir}")
    typer.echo(f"Cache directory: {settings.cache_dir}")
    typer.echo(f"Log level: {settings.log_level}")

if __name__ == "__main__":
    app()
