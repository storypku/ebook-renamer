import logging
from pathlib import Path

import pypdf

import ebook_renamer.llm as llm
import ebook_renamer.utils as ebook_utils


class PdfExtractor:
    def __init__(self, llm_client: llm.LlmClient|None = None):
        self.llm_client = llm_client

    def extract(self, fpath: Path):
        reader = pypdf.PdfReader(fpath)
        doc_info = reader.metadata
        xmp_info = reader.xmp_metadata
        pub_year = self.__parse_pub_year(
            doc_info, xmp_info
        )
        doc_title = doc_info and doc_info.title
        xmp_title = xmp_info and xmp_info.title
        print(f"{fpath}\tpub year: {pub_year}")
        if doc_title and xmp_title:
            pass
        elif doc_title:
            pass
        elif xmp_title:
            pass
        else:
            if not self.llm_client:
                self.llm_client = llm.LlmClient()

            title = self.llm_client.extract_title_of_pdf(fpath)

            logging.info('AI suggested title: [%s] for "%s"', title, fpath)

    def __parse_pub_year(self, di, xi) -> str:
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
            return ebook_utils.PUB_YEAR_MISSING
        return ts.strftime("%Y")
