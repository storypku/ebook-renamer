import argparse
import sys
from pathlib import Path

import ebook_renamer.processor as processor
from ebook_renamer.logger import setup_logger


def main() -> None:

    parser = argparse.ArgumentParser(
        description="A tool for renaming ebook (pdf, epub) files"
    )
    parser.add_argument(
        "ebooks",
        type=Path,
        nargs="+",
        help="Ebook file or directory",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subdirectories recursively",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename files (default: dry run)",
    )
    args = parser.parse_args()

    logger = setup_logger(verbose=args.verbose)

    ebooks = []
    # Collect files from all ebook paths.
    try:
        ebooks = sorted(
            [
                ebook
                for path in args.ebooks
                for ebook in processor.collect_ebooks(path, args.recursive)
            ]
        )
    except (ValueError, FileNotFoundError) as ex:
        logger.error(
            "Exception caught collecting ebooks: %s(%s)", type(ex).__name__, str(ex)
        )
        sys.exit(1)

    dry_run = not args.apply
    processor.rename_ebooks(ebooks, dry_run=dry_run)
