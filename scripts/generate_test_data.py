#!/usr/bin/env python
"""Generate synthetic test data for benchmarking system.

This script creates minimal WAV files and corresponding RTTM annotations
for testing the benchmark system without requiring large AMI downloads.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import wave
import argparse
from datetime import datetime


def generate_silent_wav(output_path: Path, duration: float = 30.0, sample_rate: int = 16000) -> None:
    """Generate a simple WAV file with minimal audio signal.
    
    Creates a WAV file with two speakers alternating (simulated by different frequencies).
    
    Args:
        output_path: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate simple audio signal
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Speaker 1: Lower frequency (simulating male voice)
    speaker1_signal = np.sin(2 * np.pi * 200 * t) * 0.1
    
    # Speaker 2: Higher frequency (simulating female voice)
    speaker2_signal = np.sin(2 * np.pi * 400 * t) * 0.1
    
    # Combine: first half speaker 1, second half speaker 2
    signal = np.zeros_like(t)
    mid_point = len(t) // 2
    signal[:mid_point] = speaker1_signal[:mid_point]
    signal[mid_point:] = speaker2_signal[mid_point:]
    
    # Add some noise to make it more realistic
    noise = np.random.normal(0, 0.01, signal.shape)
    signal = signal + noise
    
    # Normalize to 16-bit PCM range
    signal = np.int16(signal * 32767)
    
    # Write WAV file
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal.tobytes())
    
    print(f"✓ Generated WAV: {output_path} ({duration}s)")


def generate_rttm(output_path: Path, file_id: str, duration: float = 30.0, num_speakers: int = 2) -> None:
    """Generate RTTM annotation file.
    
    Args:
        output_path: Path to output RTTM file
        file_id: File identifier
        duration: Duration in seconds
        num_speakers: Number of speakers
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Simple alternating speakers
    segments = []
    if num_speakers == 2:
        # Speaker A: first half
        segments.append(f"SPEAKER {file_id} 1 0.0 {duration/2:.1f} <NA> <NA> speaker_A <NA>\n")
        # Speaker B: second half
        segments.append(f"SPEAKER {file_id} 1 {duration/2:.1f} {duration/2:.1f} <NA> <NA> speaker_B <NA>\n")
    else:
        # Simple equal distribution
        segment_duration = duration / num_speakers
        for i in range(num_speakers):
            start = i * segment_duration
            segments.append(
                f"SPEAKER {file_id} 1 {start:.1f} {segment_duration:.1f} "
                f"<NA> <NA> speaker_{chr(65+i)} <NA>\n"
            )
    
    with open(output_path, 'w') as f:
        f.writelines(segments)
    
    print(f"✓ Generated RTTM: {output_path}")


def generate_ami_test_set(data_dir: Path, num_files: int = 3, duration: float = 30.0) -> None:
    """Generate AMI-like test dataset.
    
    Args:
        data_dir: Root data directory
        num_files: Number of test files to generate
        duration: Duration of each file in seconds
    """
    print(f"\n=== Generating AMI Test Set ===")
    print(f"Directory: {data_dir}")
    print(f"Files: {num_files}")
    print(f"Duration: {duration}s each\n")
    
    # Correct structure: separate audio and annotations directories
    audio_dir = data_dir / "ami" / "audio" / "test"
    annotations_dir = data_dir / "ami" / "annotations" / "test"
    
    audio_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_files):
        file_id = f"TEST{i:04d}"
        
        # Generate WAV in audio/test/
        wav_path = audio_dir / f"{file_id}.Mix-Headset.wav"
        generate_silent_wav(wav_path, duration=duration)
        
        # Generate RTTM in annotations/test/
        rttm_path = annotations_dir / f"{file_id}.rttm"
        generate_rttm(rttm_path, file_id, duration=duration, num_speakers=2)
    
    # Create list file (like AMI-diarization-setup)
    list_file = data_dir / "ami" / "test.txt"
    with open(list_file, 'w') as f:
        for i in range(num_files):
            f.write(f"TEST{i:04d}\n")
    
    print(f"\n✓ Created list file: {list_file}")
    print(f"✓ Audio files: {num_files} in {audio_dir}")
    print(f"✓ RTTM files: {num_files} in {annotations_dir}")


def generate_sequestered_test_set(data_dir: Path, source: str = "recordings", num_files: int = 2, duration: float = 20.0) -> None:
    """Generate sequestered data test set.
    
    Args:
        data_dir: Root data directory
        source: Source name (recordings, demo, etc.)
        num_files: Number of test files
        duration: Duration of each file
    """
    print(f"\n=== Generating Sequestered Test Set ({source}) ===")
    print(f"Directory: {data_dir}")
    print(f"Files: {num_files}")
    print(f"Duration: {duration}s each\n")
    
    seq_dir = data_dir / "sequestered" / source
    audio_dir = seq_dir / "audio"
    rttm_dir = seq_dir / "rttm"
    
    audio_dir.mkdir(parents=True, exist_ok=True)
    rttm_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_files):
        file_id = f"{source}_{i:03d}"
        
        # Generate WAV
        wav_path = audio_dir / f"{file_id}.wav"
        generate_silent_wav(wav_path, duration=duration)
        
        # Generate RTTM
        rttm_path = rttm_dir / f"{file_id}.rttm"
        generate_rttm(rttm_path, file_id, duration=duration, num_speakers=2)
    
    print(f"\n✓ Total files: {num_files} audio + {num_files} RTTM")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate synthetic test data")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Root data directory (default: ./data)"
    )
    parser.add_argument(
        "--ami-files",
        type=int,
        default=3,
        help="Number of AMI test files (default: 3)"
    )
    parser.add_argument(
        "--sequestered-files",
        type=int,
        default=2,
        help="Number of sequestered test files (default: 2)"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Duration of each file in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--ami-only",
        action="store_true",
        help="Generate only AMI test set"
    )
    parser.add_argument(
        "--sequestered-only",
        action="store_true",
        help="Generate only sequestered test set"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Test Data Generator for Diarization Benchmark")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        if not args.sequestered_only:
            generate_ami_test_set(
                data_dir=args.data_dir,
                num_files=args.ami_files,
                duration=args.duration
            )
        
        if not args.ami_only:
            generate_sequestered_test_set(
                data_dir=args.data_dir,
                source="demo",
                num_files=args.sequestered_files,
                duration=args.duration * 0.7  # Slightly shorter
            )
        
        print("\n" + "=" * 60)
        print("Test data generation complete")
        print("=" * 60)
        print(f"\nData directory: {args.data_dir.absolute()}")
        print("\nNext steps:")
        print("  1. Set PYANNOTE_API_KEY in .env")
        print("  2. Run: benchmark setup")
        print("  3. Run: benchmark run-ami --models precision-2")
        print()
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
