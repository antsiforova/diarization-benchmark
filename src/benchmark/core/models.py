"""SQLAlchemy database models for the benchmark system."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class RunStatus(str, Enum):
    """Status of a benchmark run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DatasetType(str, Enum):
    """Type of dataset."""

    AMI = "ami"
    SEQUESTERED = "sequestered"


class Benchmark(Base):
    """Benchmark definition."""

    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relationships
    datasets: Mapped[list["Dataset"]] = relationship(
        "Dataset", back_populates="benchmark", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Benchmark(id={self.id}, name='{self.name}')>"


class Dataset(Base):
    """Dataset within a benchmark."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("benchmarks.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # ami, sequestered
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Relationships
    benchmark: Mapped["Benchmark"] = relationship("Benchmark", back_populates="datasets")
    audio_files: Mapped[list["AudioFile"]] = relationship(
        "AudioFile", back_populates="dataset", cascade="all, delete-orphan"
    )
    runs: Mapped[list["Run"]] = relationship(
        "Run", back_populates="dataset", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_datasets_benchmark_id", "benchmark_id"),
        Index("ix_datasets_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name='{self.name}', type='{self.type}')>"


class AudioFile(Base):
    """Audio file within a dataset."""

    __tablename__ = "audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[float | None] = mapped_column(Float)  # Duration in seconds
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="audio_files")
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="audio_file", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_audio_files_dataset_id", "dataset_id"),
        Index("ix_audio_files_file_path", "file_path"),
    )

    def __repr__(self) -> str:
        return f"<AudioFile(id={self.id}, file_path='{self.file_path}')>"


class Annotation(Base):
    """Ground truth annotation for an audio file."""

    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audio_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False
    )
    ground_truth: Mapped[str] = mapped_column(Text, nullable=False)  # RTTM format
    format: Mapped[str] = mapped_column(String(50), default="rttm", nullable=False)
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Relationships
    audio_file: Mapped["AudioFile"] = relationship("AudioFile", back_populates="annotations")

    # Indexes
    __table_args__ = (Index("ix_annotations_audio_file_id", "audio_file_id"),)

    def __repr__(self) -> str:
        return f"<Annotation(id={self.id}, audio_file_id={self.audio_file_id})>"


class Run(Base):
    """Benchmark run for a specific model and dataset."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Model configuration
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="runs")
    results: Mapped[list["Result"]] = relationship(
        "Result", back_populates="run", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_runs_dataset_id", "dataset_id"),
        Index("ix_runs_model_name", "model_name"),
        Index("ix_runs_status", "status"),
        Index("ix_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Run(id={self.id}, model='{self.model_name}', status='{self.status}')>"


class Result(Base):
    """Evaluation result for a specific run."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    audio_file_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("audio_files.id", ondelete="SET NULL")
    )  # Null for aggregate metrics
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)  # DER, JER, etc.
    value: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # Detailed breakdown (miss, false alarm, confusion, etc.)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="results")

    # Indexes
    __table_args__ = (
        Index("ix_results_run_id", "run_id"),
        Index("ix_results_metric_name", "metric_name"),
        Index("ix_results_audio_file_id", "audio_file_id"),
    )

    def __repr__(self) -> str:
        return f"<Result(id={self.id}, metric='{self.metric_name}', value={self.value})>"
