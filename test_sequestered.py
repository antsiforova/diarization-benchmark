#!/usr/bin/env python
"""Quick test script to run diarization on sequestered files without database."""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Environment variables loaded automatically by pydantic-settings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from benchmark.evaluation.mock_diarization import MockDiarizer
from benchmark.evaluation.metrics import DiarizationMetrics
from benchmark.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging("INFO", "text")
logger = get_logger(__name__)


async def main():
    """Run diarization on conversation recording sequestered files."""
    
    # Audio files
    audio_dir = Path("data/sequestered/recordings/audio")
    annotation_dir = Path("data/sequestered/recordings/annotations")
    
    audio_files = sorted([f.name for f in audio_dir.glob("*.wav")])
    
    if not audio_files:
        logger.error(f"No audio files found in {audio_dir}")
        return

    api_client = MockDiarizer(cache_dir=Path("cache"))
    
    metrics_calculator = DiarizationMetrics()
    
    # Results storage
    all_results = []
    
    logger.info(f"Starting SEQUESTERED benchmark on {len(audio_files)} conversation recording files...")
    logger.info(f"Mock diarization mode")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    # Process each file
    for i, audio_file in enumerate(audio_files, 1):
        audio_path = audio_dir / audio_file
        annotation_path = annotation_dir / audio_file.replace(".wav", ".rttm")
        
        if not audio_path.exists():
            logger.warning(f"Audio file not found: {audio_path}")
            continue
            
        if not annotation_path.exists():
            logger.warning(f"Annotation file not found: {annotation_path}")
            continue
        
        logger.info(f"\n[{i}/{len(audio_files)}] Processing: {audio_file}")
        logger.info(f"  Audio: {audio_path}")
        logger.info(f"  Reference: {annotation_path}")
        
        try:
            file_start = datetime.now()
            
            # Call API to get hypothesis
            logger.info("  Calling diarization API...")
            hypothesis_response = await api_client.diarize(
                audio_path=audio_path,
                model=model_name,
            )
            
            # Convert to annotations
            logger.info("  Computing metrics...")
            reference_annotation = metrics_calculator.rttm_to_annotation(annotation_path)
            hypothesis_annotation = metrics_calculator.hypothesis_to_annotation(hypothesis_response)
            
            # Compute metrics
            der_result = metrics_calculator.compute_der(reference_annotation, hypothesis_annotation)
            jer_result = metrics_calculator.compute_jer(reference_annotation, hypothesis_annotation)
            
            file_duration = (datetime.now() - file_start).total_seconds()
            
            # Display results
            der = der_result["DER"]
            jer = jer_result["JER"]
            
            logger.info(f"  DER: {der:.4f}")
            logger.info(f"  JER: {jer:.4f}")
            logger.info(f"  Time: {file_duration:.2f}s")
            
            all_results.append({
                "file": audio_file,
                "der": der,
                "jer": jer,
                "duration": file_duration,
            })
            
        except Exception as e:
            logger.error(f"  Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            all_results.append({
                "file": audio_file,
                "error": str(e),
            })
    
    # Summary
    total_duration = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "=" * 80)
    logger.info("SEQUESTERED DATA SUMMARY")
    logger.info("=" * 80)
    
    successful = [r for r in all_results if "error" not in r]
    failed = [r for r in all_results if "error" in r]
    
    if successful:
        avg_der = sum(r["der"] for r in successful) / len(successful)
        avg_jer = sum(r["jer"] for r in successful) / len(successful)
        min_der = min(r["der"] for r in successful)
        max_der = max(r["der"] for r in successful)
        
        logger.info(f"\nSuccessful: {len(successful)}/{len(audio_files)}")
        logger.info(f"\nDiarization Error Rate (DER):")
        logger.info(f"  Mean: {avg_der:.4f}")
        logger.info(f"  Min:  {min_der:.4f}")
        logger.info(f"  Max:  {max_der:.4f}")
        
        logger.info(f"\nJaccard Error Rate (JER):")
        logger.info(f"  Mean: {avg_jer:.4f}")
        
        logger.info(f"\nThreshold Check (Conversation recordings vary by conditions):")
        if avg_der < 0.20:
            logger.info(f"  Excellent DER (< 0.20)")
        elif avg_der < 0.30:
            logger.info(f"  Good DER (< 0.30)")
        else:
            logger.info(f"  DER indicates challenging conditions (> 0.30)")
    
    if failed:
        logger.info(f"\nFailed: {len(failed)}/{len(audio_files)}")
        for r in failed:
            logger.info(f"  - {r['file']}: {r['error']}")
    
    logger.info(f"\nTotal time: {total_duration:.2f}s")
    logger.info("=" * 80)
    
    logger.info("\nDETAILED RESULTS:")
    for r in all_results:
        if "error" not in r:
            logger.info(f"  {r['file']:30s} DER={r['der']:.4f}  JER={r['jer']:.4f}  ({r['duration']:.1f}s)")
        else:
            logger.info(f"  {r['file']:30s} ERROR: {r['error']}")


if __name__ == "__main__":
    asyncio.run(main())
