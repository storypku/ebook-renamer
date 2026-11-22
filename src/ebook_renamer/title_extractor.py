import logging
import re
from pathlib import Path

import ebooklib.epub as epub
import pypdf
from ebooklib.book import EpubBook
from pypdf.xmp import XmpInformation

import ebook_renamer.llm as llm
import ebook_renamer.utils as ebook_utils
from ebook_renamer.utils import EbookInfo

logger = logging.getLogger(__name__)


class EbookExtractor:
    def extract(self, fpath: Path) -> EbookInfo:
        logger.exception("Not implemented yet")
        return EbookInfo(title="")


class PdfExtractor(EbookExtractor):
    def __init__(self, llm_client: llm.LlmClient | None = None):
        self.llm_client = llm_client

    @staticmethod
    def _extract_pub_year_of_pdf(
        di: pypdf.DocumentInformation | None, xi: XmpInformation | None
    ) -> str:
        if di and xi:
            ts = (
                di.modification_date
                or xi.xmp_modify_date
                or di.creation_date
                or xi.xmp_create_date
            )
        elif di:
            ts = di.modification_date or di.creation_date
        elif xi:
            ts = xi.xmp_modify_date or xi.xmp_create_date
        else:
            ts = None
        return ts.strftime("%Y") if ts else ebook_utils.PUB_YEAR_MISSING

    def extract(self, fpath: Path) -> EbookInfo:
        reader = pypdf.PdfReader(fpath)
        doc_info = reader.metadata
        xmp_info = reader.xmp_metadata

        pub_year = PdfExtractor._extract_pub_year_of_pdf(doc_info, xmp_info)

        doc_title: str | None = None
        if doc_info is not None:
            doc_title = doc_info.title

        xmp_title: str | None = None
        if xmp_info is not None and xmp_info.dc_title is not None:
            xmp_title = xmp_info.dc_title.get("x-default")

        raw_title: str

        if doc_title and xmp_title:
            if doc_title != xmp_title:
                logger.warning("Two titles differ: %s vs %s", doc_title, xmp_title)

            raw_title = xmp_title
            logger.debug("Title from DocInfo: %s", doc_title)

        elif doc_title:
            raw_title = doc_title
            logger.debug("Title from DocInfo: %s", doc_title)

        elif xmp_title:
            raw_title = xmp_title
            logger.debug("Title from XmpInfo: %s", xmp_title)

        else:
            if not self.llm_client:
                self.llm_client = llm.LlmClient()

            raw_title = self.llm_client.extract_title_of_pdf(fpath)
            logger.debug("Title suggested by AI: [%s] for [%s]", raw_title, fpath)

        title, subtitle, edition = ebook_utils.sanitize_ebook(raw_title)

        return EbookInfo(
            title=title,
            subtitle=subtitle,
            etype=ebook_utils.EbookType.PDF,
            pub_year=pub_year,
            edition=edition,
        )


class EpubExtractor(EbookExtractor):
    def __init__(self, llm_client: llm.LlmClient | None = None):
        self.llm_client = llm_client

    @staticmethod
    def _extract_dc_title(book: EpubBook) -> str | None:
        # Extract title from EPUB Dublin Core metadata.
        title_entries = book.get_metadata("DC", "title")
        for value, _ in title_entries:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _extract_pub_year(book: EpubBook) -> str:
        pub_year = "0000"  # ebook_utils.PUB_YEAR_MISSING
        date_entries = book.get_metadata("DC", "date")
        for value, _ in date_entries:
            match = re.search(r"\b(?:19|20)\d{2}\b", value)
            if match:
                pub_year = match.group()
                break
        return pub_year

    def extract(self, fpath: Path) -> EbookInfo:
        book = epub.read_epub(fpath)
        raw_title = EpubExtractor._extract_dc_title(book)
        pub_year = EpubExtractor._extract_pub_year(book)

        # Fall back to LLM if EPUB metadata has no title.
        if not raw_title:
            if not self.llm_client:
                self.llm_client = llm.LlmClient()
            raw_title = self.llm_client.extract_title_of_epub(fpath)
            logger.debug("Title suggested by AI: [%s] for [%s]", raw_title, fpath)
        else:
            logger.debug(f"Title from EPUB metadata: {raw_title}")

        title, subtitle, edition = ebook_utils.sanitize_ebook(raw_title)
        return EbookInfo(
            title=title,
            subtitle=subtitle,
            etype=ebook_utils.EbookType.EPUB,
            pub_year=pub_year,
            edition=edition,
        )
