"""Mock diarization client for testing and demonstrations."""

import wave
from pathlib import Path
from typing import Any

from benchmark.utils.logging import get_logger

logger = get_logger(__name__)


class MockDiarizer:
    """Mock diarization client - generates simulated results.
    
    For production, replace with real Pyannote API integration
    (requires cloud file storage for audio URLs).
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize mock diarizer.
        
        Args:
            cache_dir: Optional cache directory (created if doesn't exist)
        """
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """Close client (no-op for mock)."""
        pass

    def _generate_demo_response(self, audio_path: Path) -> dict[str, Any]:
        """Generate simulated diarization response.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Simulated diarization result
        """
        import wave

        # Try to get actual duration from WAV file
        try:
            with wave.open(str(audio_path), 'r') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate)
        except Exception:
            duration = 30.0  # Fallback

        # Generate realistic-looking segments (2 speakers alternating)
        segments = [
            {
                "start": 0.0,
                "end": duration * 0.45,
                "speaker": "SPEAKER_00",
                "confidence": 0.92
            },
            {
                "start": duration * 0.45,
                "end": duration * 0.48,
                "speaker": "OVERLAP",  # Small overlap
                "confidence": 0.78
            },
            {
                "start": duration * 0.48,
                "end": duration,
                "speaker": "SPEAKER_01",
                "confidence": 0.89
            }
        ]

        return {
            "segments": segments,
            "num_speakers": 2,
            "duration": duration,
            "model": "mock-demo",
            "mock_mode": True
        }

    async def diarize(self, audio_path: Path) -> dict[str, Any]:
        """Generate mock diarization for audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Mock diarization result with speaker segments
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Mock diarization: {audio_path.name}")
        
        return self._generate_demo_response(audio_path)