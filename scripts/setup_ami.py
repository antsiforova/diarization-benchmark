#!/usr/bin/env python
"""Setup AMI dataset with automated annotation extraction and audio download instructions.

This script automates the AMI dataset setup process:
1. Clones/updates the AMI-diarization-setup repository
2. Extracts RTTM annotations for specified number of test files
3. Checks for existing audio files
4. Provides download instructions if audio files are missing

Usage:
    python scripts/setup_ami.py --num-files 4
    python scripts/setup_ami.py --num-files 10 --force-update
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark.utils.logging import get_logger, setup_logging

setup_logging("INFO", "text")
logger = get_logger(__name__)


class AMISetup:
    """Automated AMI dataset setup."""

    REPO_URL = "https://github.com/pyannote/AMI-diarization-setup.git"
    AMI_DOWNLOAD_URL = "https://groups.inf.ed.ac.uk/ami/download/"

    def __init__(self, base_dir: Path):
        """Initialize AMI setup.
        
        Args:
            base_dir: Base directory for AMI data (e.g., data/ami)
        """
        self.base_dir = base_dir
        self.repo_path = base_dir / "AMI-diarization-setup"
        self.audio_dir = base_dir / "audio" / "test"
        self.annotation_dir = base_dir / "annotations" / "test"

    async def setup_repository(self, force_update: bool = False) -> Path:
        """Clone or update AMI diarization setup repository.
        
        Args:
            force_update: Force git pull even if repo exists
            
        Returns:
            Path to cloned repository
        """
        if self.repo_path.exists():
            if force_update:
                logger.info("Updating AMI repository...")
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info("Repository updated successfully")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to update repository: {e.stderr}")
                    raise
            else:
                logger.info("AMI repository already exists")
        else:
            logger.info(f"Cloning AMI repository from {self.REPO_URL}...")
            try:
                self.base_dir.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    ["git", "clone", self.REPO_URL, str(self.repo_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info("Repository cloned successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository: {e.stderr}")
                raise

        return self.repo_path

    def get_test_files(self, num_files: int, offset: int = 0, file_ids: list[str] | None = None) -> list[str]:
        """Get list of test files from AMI repository.
        
        Args:
            num_files: Number of files to return (if file_ids not specified)
            offset: Offset in test.txt to start from (default: 0)
            file_ids: Specific file IDs to use (overrides num_files/offset)
            
        Returns:
            List of file IDs
        """
        # If specific file IDs provided, use them
        if file_ids:
            logger.info(f"Using specified file IDs: {', '.join(file_ids)}")
            return file_ids
        
        # Otherwise read from test.txt
        test_list = self.repo_path / "only_words" / "lists" / "test.txt"
        
        if not test_list.exists():
            raise FileNotFoundError(f"Test file list not found: {test_list}")

        with open(test_list, "r") as f:
            all_files = [line.strip() for line in f if line.strip()]

        # Take N files starting from offset
        files = all_files[offset:offset + num_files]
        logger.info(f"Selected {len(files)} files from test set (offset: {offset})")
        
        return files

    def extract_annotations(self, file_ids: list[str]) -> dict[str, Path]:
        """Extract RTTM annotations from repository.
        
        Args:
            file_ids: List of file IDs to extract
            
        Returns:
            Dictionary mapping file_id -> annotation path
        """
        self.annotation_dir.mkdir(parents=True, exist_ok=True)
        annotations = {}

        rttm_dir = self.repo_path / "only_words" / "rttms" / "test" 

        logger.info(f"📝 Extracting annotations...")

        for file_id in file_ids:
            rttm_file = rttm_dir / f"{file_id}.rttm"
            if rttm_file.exists():
                dest = self.annotation_dir / f"{file_id}.Mix-Headset.rttm"
                dest.write_text(rttm_file.read_text())
                annotations[file_id] = dest
            else:
                logger.warning(f"RTTM not found: {file_id}")

        logger.info(f"Extracted {len(annotations)}/{len(file_ids)} annotations")
        return annotations

    def check_audio_files(self, file_ids: list[str]) -> tuple[dict[str, Path], list[str]]:
        """Check for existing audio files.
        
        Args:
            file_ids: List of file IDs to check
            
        Returns:
            Tuple of (existing files dict, missing files list)
        """
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        existing = {}
        missing = []

        for file_id in file_ids:
            audio_file = self.audio_dir / f"{file_id}.Mix-Headset.wav"
            if audio_file.exists():
                existing[file_id] = audio_file
            else:
                missing.append(file_id)

        return existing, missing

    def print_download_instructions(self, missing_files: list[str]):
        """Print instructions for downloading missing audio files.
        
        Args:
            missing_files: List of missing file IDs
        """
        if not missing_files:
            return

        logger.info("=" * 80)
        logger.info("AUDIO FILES MISSING - MANUAL DOWNLOAD REQUIRED")
        logger.info("=" * 80)
        logger.info("")
        logger.info("AMI Corpus requires registration and license agreement.")
        logger.info("")
        logger.info("Step 1: Register and download")
        logger.info(f"   Visit: {self.AMI_DOWNLOAD_URL}")
        logger.info("   Accept license agreement")
        logger.info("")
        logger.info("Step 2: Download these files (Mix-Headset format):")
        for file_id in missing_files:
            logger.info(f"   - {file_id}.Mix-Headset.wav")
        logger.info("")
        logger.info("Step 3: Place downloaded files in:")
        logger.info(f"   {self.audio_dir.absolute()}")
        logger.info("")
        logger.info("Alternative: Use AMI download scripts")
        logger.info(f"   cd {self.repo_path / 'pyannote'}")
        logger.info("   bash download_ami_mini.sh")
        logger.info("")
        logger.info("=" * 80)

    async def setup(
        self, 
        num_files: int = 4, 
        offset: int = 0,
        file_ids: list[str] | None = None,
        force_update: bool = False
    ):
        """Run complete AMI setup.
        
        Args:
            num_files: Number of test files to prepare
            offset: Offset in test list to start from
            file_ids: Specific file IDs to use (overrides num_files/offset)
            force_update: Force repository update
        """
        logger.info("=" * 80)
        logger.info("AMI DATASET SETUP")
        logger.info("=" * 80)
        if file_ids:
            logger.info(f"Target: {len(file_ids)} specified files")
        else:
            logger.info(f"Target: {num_files} test files (offset: {offset})")
        logger.info("")

        # Step 1: Setup repository
        await self.setup_repository(force_update=force_update)

        # Step 2: Get file list
        selected_files = self.get_test_files(num_files, offset=offset, file_ids=file_ids)

        # Step 3: Extract annotations
        annotations = self.extract_annotations(selected_files)

        # Step 4: Check audio files
        existing_audio, missing_audio = self.check_audio_files(selected_files)

        # Step 5: Report status
        total_files = len(selected_files)
        logger.info("")
        logger.info("=" * 80)
        logger.info("SETUP SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Repository: {self.repo_path}")
        logger.info(f"Annotations: {len(annotations)}/{total_files} extracted")
        logger.info(f"Audio files: {len(existing_audio)}/{total_files} found")
        logger.info("")

        # Step 6: Print download instructions if needed
        if missing_audio:
            self.print_download_instructions(missing_audio)
        else:
            logger.info("🎉 Setup complete! All files ready for benchmarking.")
            logger.info("")
            logger.info("Next steps:")
            logger.info("   python run_and_save.py --dataset ami")
            logger.info("   python test_ami_files.py")
            logger.info("")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AMI dataset with automated annotation extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup first 4 test files (default)
  python scripts/setup_ami.py
  
  # Setup 10 test files starting from offset 5
  python scripts/setup_ami.py --num-files 10 --offset 5
  
  # Setup specific files (e.g., EN2002 series)
  python scripts/setup_ami.py --file-ids EN2002a EN2002b EN2002c EN2002d
  
  # Force update repository
  python scripts/setup_ami.py --force-update
        """
    )
    parser.add_argument(
        "--num-files",
        type=int,
        default=4,
        help="Number of test files to prepare (default: 4)"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset in test list to start from (default: 0)"
    )
    parser.add_argument(
        "--file-ids",
        nargs="+",
        help="Specific file IDs to setup (e.g., EN2002a EN2002b)"
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Force git pull even if repository exists"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("data/ami"),
        help="Base directory for AMI data (default: data/ami)"
    )

    args = parser.parse_args()

    # Validate num_files
    if not args.file_ids and args.num_files < 1:
        logger.error("num-files must be at least 1")
        sys.exit(1)
    
    if not args.file_ids and args.num_files > 20:
        logger.warning(f"Requesting {args.num_files} files - this may be slow to download")

    # Run setup
    setup = AMISetup(args.base_dir)
    await setup.setup(
        num_files=args.num_files,
        offset=args.offset,
        file_ids=args.file_ids,
        force_update=args.force_update
    )


if __name__ == "__main__":
    asyncio.run(main())
