import logging
from pathlib import Path

import ebook_renamer.llm as llm
import ebook_renamer.title_extractor as title_extractor
import ebook_renamer.utils as ebook_utils


def collect_ebooks(
    path: Path,
    recursive: bool,
) -> list[Path]:
    """Collect ebook files from a file or directory."""
    ebooks = []
    if path.is_file():
        if not ebook_utils.is_ebook(path):
            raise ValueError("Not an ebook: %s", path)
        else:
            return [path]

    if not path.is_dir():
        raise FileNotFoundError(path)

    pattern = "**/*" if recursive else "*"
    ebooks = [p for p in path.glob(pattern) if ebook_utils.is_ebook(p)]
    return sorted(ebooks)

def rename_ebook(path: Path, llm_client: llm.LlmClient | None = None, dry_run=True):
    # TODO(story): next time work here
    if not ebook_utils.is_ebook(path):
        raise ValueError("Not an ebook: %s", path)

    if ebook_utils.is_pdf(path):
        pdf_xtor = title_extractor.PdfExtractor(llm_client)
        pdf_xtor.extract(path)



def rename_ebooks(paths: list[Path], dry_run=True):
    """Rename multiple ebooks, reusing one LLM client."""
    llm = None

    num_books = len(paths)
    failures = 0

    for path in paths:
        try:
            # Initialize LLM lazily, only when needed.
            rename_ebook(path, llm)
        except (RuntimeError, ValueError) as ex:
            logging.exception(f"Failed to rename %s: {path} {str(ex)}")
            failures += 1

    logging.info(
        "Finished processing ebooks: %d succeeded, %d failed",
        num_books - failures,
        failures,
    )
