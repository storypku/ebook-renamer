import enum
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import ebooklib.epub as epub
import pypdf
from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT as EBOOK_ITEM_DOCUMENT

SUPPORTED_EXTENSIONS = [".pdf", ".epub"]

KNOWN_EDITIONS = [
    "First",
    "Second",
    "Third",
    "Fourth",
    "Fifth",
    "Sixth",
    "Seventh",
    "Eighth",
    "Ninth",
    "Tenth",
    "Eleventh",
    "Twelfth",
    "Thirteenth",
    "Fourteenth",
    "Fifteenth",
    "Sixteenth",
    "Seventeenth",
    "Eighteenth",
    "Nineteenth",
    "Twentieth",
]

PUB_YEAR_MISSING = "0000"

# Special characters
EM_DASH = chr(0x2014)
COLON = ":"

logger = logging.getLogger(__name__)


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


SUFFIX_MAP = {
    f"{w} Edition": f"{ordinal(i + 1)}" for (i, w) in enumerate(KNOWN_EDITIONS)
}


class EbookType(enum.IntEnum):
    PDF = 1
    EPUB = 2


@dataclass
class EbookInfo:
    title: str
    subtitle: str | None = None
    etype: EbookType = EbookType.PDF
    pub_year: str = PUB_YEAR_MISSING
    edition: str | None = None

    def __repr__(self) -> str:
        title = f"{self.title}:{self.subtitle}" if self.subtitle else self.title
        return (
            f"EbookInfo("
            f"title={title}, "
            f"etype={self.etype.name.lower()}, "
            f"pub_year={self.pub_year}, "
            f"edition={self.edition!r}"
            f")"
        )

    def canonical_filename(self) -> str:
        ans = ".".join(self.title.split())
        if self.subtitle:
            ans += ".{}".format(".".join(self.subtitle.split()))
        if self.edition:
            ans += f".{self.edition}"
        ans += f".{self.pub_year}.{self.etype.name.lower()}"
        return ans


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


def extract_text_from_first_pages_of_epub(fpath: Path, num_pages: int) -> str:
    """Extract text from the first n pages of an ePub."""

    book = epub.read_epub(fpath)
    texts = []

    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None or item.get_type() != EBOOK_ITEM_DOCUMENT:
            continue
        try:
            content = item.get_content()
            soup = BeautifulSoup(content, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)

            if not text:
                continue
            texts.append(text)
            if len(texts) >= num_pages:
                break
        except (KeyError, OSError) as exc:
            logger.exception(f"Skipping {item.get_name()}: {exc}")

    return "\n".join(texts)


def normalize(text: str) -> str:
    if text.isupper():
        return " ".join(word.capitalize() for word in text.split())
    return text


def sanitize_ebook(s: str) -> tuple[str, str | None, str | None]:
    subtitle = None
    edition = None
    s = re.sub(r"\s*\([^()]*\)", "", s).strip()
    if s.endswith(" Edition"):
        for k, v in SUFFIX_MAP.items():
            if s.endswith(k):
                edition = v
                s = s[: -len(k)].rstrip()
    s = s.replace(EM_DASH, " ").replace("-", " ").replace(",", " ").replace("'", "")
    s = re.sub(r"\s+", " ", normalize(s))
    if COLON in s:
        title, subtitle = s.split(COLON)
    else:
        title = s
    return (title, subtitle, edition)
