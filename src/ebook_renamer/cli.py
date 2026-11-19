import argparse
import logging
import sys
from pathlib import Path

from ebook_renamer import processor


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
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
        "--apply",
        action="store_true",
        help="Actually rename files (default: dry run)",
    )
    args = parser.parse_args()

    dry_run = not args.apply

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
        logging.error(f"Exception caught collecting ebooks: {ex}")
        sys.exit(1)

    processor.rename_ebooks(ebooks, dry_run=dry_run)
