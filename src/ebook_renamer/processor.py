import logging
from pathlib import Path

import ebook_renamer.llm as llm
import ebook_renamer.title_extractor as title_extractor
import ebook_renamer.utils as ebook_utils

logger = logging.getLogger(__name__)


def collect_ebooks(
    path: Path,
    recursive: bool,
) -> list[Path]:
    """Collect ebook files from a file or directory."""
    ebooks = []
    if path.is_file():
        if not ebook_utils.is_ebook(path):
            raise ValueError(f"Not an ebook: {path}")
        else:
            return [path]

    if not path.is_dir():
        raise FileNotFoundError(path)

    pattern = "**/*" if recursive else "*"
    ebooks = [p for p in path.glob(pattern) if ebook_utils.is_ebook(p)]
    return sorted(ebooks)


def rename_ebook(fpath: Path, llm_client: llm.LlmClient | None = None, dry_run=True):
    if not ebook_utils.is_ebook(fpath):
        raise ValueError(f"Not an ebook: {fpath}")

    ebook: ebook_utils.EbookInfo

    if ebook_utils.is_pdf(fpath):
        pdf_extractor = title_extractor.PdfExtractor(llm_client)
        ebook = pdf_extractor.extract(fpath)
    elif ebook_utils.is_epub(fpath):
        epub_extractor = title_extractor.EpubExtractor(llm_client)
        ebook = epub_extractor.extract(fpath)
    else:
        raise RuntimeError(f"Logic can't reach here: {fpath}")

    new_fn = ebook.canonical_filename()
    if dry_run:
        logger.info("Dry-run-only: file [%s] will be renamed to [%s].", fpath, new_fn)
        return

    new_path = fpath.with_name(new_fn)
    if fpath == new_path:
        logger.warning("No-op: File already well-renamed: %s", fpath)
        return

    if new_path.exists():
        raise FileExistsError(f"File already exists: {new_path}")

    fpath.rename(new_path)
    logger.info("Applied: file [%s] was renamed to [%s]", fpath, new_path)


def rename_ebooks(paths: list[Path], dry_run=True):
    """Rename multiple ebooks, reusing one LLM client."""
    llm = None

    num_books = len(paths)
    failures = 0

    for fpath in paths:
        try:
            # Initialize LLM lazily, only when needed.
            rename_ebook(fpath, llm, dry_run=dry_run)
        except Exception as ex:
            logger.exception(f"Failed to rename {fpath}: {ex}")
            failures += 1

    if num_books > 1:
        logger.info(
            "Finished processing ebooks: %d succeeded, %d failed",
            num_books - failures,
            failures,
        )
