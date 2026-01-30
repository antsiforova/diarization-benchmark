"""Metrics computation for diarization evaluation."""

from pathlib import Path
from typing import Any

from pyannote.core import Annotation, Segment
from pyannote.metrics.diarization import DiarizationErrorRate, JaccardErrorRate

from benchmark.utils.logging import get_logger

logger = get_logger(__name__)


class DiarizationMetrics:
    """Compute diarization metrics (DER, JER, etc.)."""

    @staticmethod
    def rttm_to_annotation(rttm_path: Path) -> Any:
        """Convert RTTM file to pyannote Annotation object.

        Args:
            rttm_path: Path to RTTM file

        Returns:
            pyannote.core.Annotation object
        """
        
        annotation = Annotation()

        with open(rttm_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) < 8 or parts[0] != "SPEAKER":
                    continue

                # RTTM format: SPEAKER file channel start duration <NA> <NA> speaker <NA>
                start = float(parts[3])
                duration = float(parts[4])
                speaker = parts[7]

                segment = Segment(start, start + duration)
                annotation[segment] = speaker

        return annotation

    @staticmethod
    def hypothesis_to_annotation(hypothesis: dict[str, Any]) -> Any:
        """Convert hypothesis to pyannote Annotation object.

        Args:
            hypothesis: Diarization hypothesis

        Returns:
            pyannote.core.Annotation object
        """
        annotation = Annotation()

        # Expected format: {"segments": [{"start": ..., "end": ..., "speaker": ...}, ...]}
        for segment_data in hypothesis.get("segments", []):
            start = segment_data["start"]
            end = segment_data["end"]
            speaker = segment_data["speaker"]

            segment = Segment(start, end)
            annotation[segment] = speaker

        return annotation

    @staticmethod
    def compute_der(
        reference: Any,
        hypothesis: Any,
        collar: float = 0.25,
        skip_overlap: bool = False,
    ) -> dict[str, float]:
        """Compute Diarization Error Rate.

        Args:
            reference: Reference annotation
            hypothesis: Hypothesis annotation
            collar: Collar size in seconds
            skip_overlap: Skip overlapping speech regions

        Returns:
            Dictionary with DER metrics
        """
        metric = DiarizationErrorRate(collar=collar, skip_overlap=skip_overlap)

        # Compute DER
        der_value = metric(reference, hypothesis)

        # Get components
        components = metric.compute_components(reference, hypothesis)

        # Handle different versions of pyannote.metrics key names
        result = {
            "DER": float(der_value),
            "miss": float(components.get("false negative", components.get("miss", 0.0))),
            "false_alarm": float(components.get("false positive", components.get("false alarm", 0.0))),
            "confusion": float(components.get("confusion", 0.0)),
            "total": float(components.get("total", 1.0)),
        }

        logger.debug(f"DER: {result['DER']:.3f} (components: {result})")
        return result

    @staticmethod
    def compute_jer(reference: Any, hypothesis: Any) -> dict[str, float]:
        """Compute Jaccard Error Rate.

        Args:
            reference: Reference annotation
            hypothesis: Hypothesis annotation

        Returns:
            Dictionary with JER metric
        """

        metric = JaccardErrorRate()
        jer_value = metric(reference, hypothesis)

        result = {"JER": float(jer_value)}

        logger.debug(f"JER: {result['JER']:.3f}")
        return result

    @staticmethod
    def compute_all_metrics(
        reference_rttm: Path,
        hypothesis: dict[str, Any],
        collar: float = 0.25,
        skip_overlap: bool = False,
    ) -> dict[str, Any]:
        """Compute all diarization metrics.

        Args:
            reference_rttm: Path to reference RTTM file
            hypothesis: Hypothesis from API
            collar: Collar size for DER
            skip_overlap: Skip overlapping speech for DER

        Returns:
            Dictionary with all metrics
        """
        # Convert to annotations
        reference = DiarizationMetrics.rttm_to_annotation(reference_rttm)
        hypothesis_ann = DiarizationMetrics.hypothesis_to_annotation(hypothesis)

        # Compute metrics
        der_metrics = DiarizationMetrics.compute_der(
            reference, hypothesis_ann, collar, skip_overlap
        )
        jer_metrics = DiarizationMetrics.compute_jer(reference, hypothesis_ann)

        # Combine results
        metrics = {**der_metrics, **jer_metrics}

        logger.info(
            f"Metrics computed - DER: {metrics['DER']:.3f}, JER: {metrics['JER']:.3f}"
        )

        return metrics


class MetricAggregator:
    """Aggregate metrics across multiple files."""

    def __init__(self) -> None:
        """Initialize metric aggregator."""
        self.metrics: list[dict[str, Any]] = []

    def add(self, metrics: dict[str, Any], file_id: str | None = None) -> None:
        """Add metrics for a file.

        Args:
            metrics: Metrics dictionary
            file_id: Optional file identifier
        """
        self.metrics.append({"metrics": metrics, "file_id": file_id})

    def aggregate(self) -> dict[str, Any]:
        """Compute aggregate statistics.

        Returns:
            Dictionary with mean, std, min, max for each metric
        """
        if not self.metrics:
            return {}

        import statistics

        # Collect all metric values
        metric_values: dict[str, list[float]] = {}

        for item in self.metrics:
            for metric_name, value in item["metrics"].items():
                if isinstance(value, (int, float)):
                    if metric_name not in metric_values:
                        metric_values[metric_name] = []
                    metric_values[metric_name].append(float(value))

        # Compute statistics
        aggregated: dict[str, Any] = {}

        for metric_name, values in metric_values.items():
            aggregated[f"{metric_name}_mean"] = statistics.mean(values)
            aggregated[f"{metric_name}_std"] = (
                statistics.stdev(values) if len(values) > 1 else 0.0
            )
            aggregated[f"{metric_name}_min"] = min(values)
            aggregated[f"{metric_name}_max"] = max(values)
            aggregated[f"{metric_name}_median"] = statistics.median(values)

        aggregated["num_files"] = len(self.metrics)

        logger.info(f"Aggregated metrics from {len(self.metrics)} files")
        return aggregated

    def get_per_file_metrics(self) -> list[dict[str, Any]]:
        """Get per-file metrics.

        Returns:
            List of per-file metrics
        """
        return self.metrics
