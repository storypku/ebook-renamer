import enum
from dataclasses import dataclass
from pathlib import Path

import pypdf

SUPPORTED_EXTENSIONS = [".pdf", ".epub"]

class EbookType(enum.IntEnum):
    PDF = 1
    EPUB = 2

PUB_YEAR_MISSING = "0000"

@dataclass
class EbookInfo:
    title: str
    sub_title: str = ""
    etype: EbookInfo = EbookType.PDF
    pub_year: str = PUB_YEAR_MISSING
    edition: str | None = None

def is_ebook(p: Path):
    return p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS


def is_pdf(path: Path):
    return path.is_file() and path.suffix.lower() == ".pdf"


def is_epub(path: Path):
    return path.is_file() and path.suffix.lower() == ".epub"


def extract_text_from_first_pages_of_pdf(fpath: Path, num_pages: int) -> str:
    """Extract text from the first n pages of a PDF."""

    reader = pypdf.PdfReader(fpath)

    num_pages = min(num_pages, len(reader.pages))
    result = []
    for page in reader.pages[:num_pages]:
        text = page.extract_text()
        if text:
            result.append(text)

    return "\n".join(result)
