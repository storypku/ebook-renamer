import logging
import os
from pathlib import Path

import openai

import ebook_renamer.utils as ebook_utils
from ebook_renamer.utils import EbookType

MAX_TEXT_LENGTH = 4096
MAX_NUMBER_OF_PAGES = 3

PROMPT_TEMPLATE = """
Below is the text from the first few pages of {}.
Please extract the title of this document. If edition
information provided, append it into the title in a
format such as "Second Edition" or "Third Edition".

Return only the title text, without any explanation or punctuation.

Text content:
{}
"""

logger = logging.getLogger(__name__)


class LlmClient:
    """Client for extracting document titles using an LLM."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

    def extract_title_of_pdf(
        self, pdf_path: Path, num_pages: int = MAX_NUMBER_OF_PAGES
    ) -> str:
        text = ebook_utils.extract_text_from_first_pages_of_pdf(
            pdf_path, num_pages=num_pages
        )
        return self._extract_title(text[:MAX_TEXT_LENGTH], EbookType.PDF)

    def extract_title_of_epub(
        self, pdf_path: Path, num_pages: int = MAX_NUMBER_OF_PAGES
    ) -> str:
        text = ebook_utils.extract_text_from_first_pages_of_epub(
            pdf_path, num_pages=num_pages
        )
        return self._extract_title(text[:MAX_TEXT_LENGTH], EbookType.EPUB)

    def _extract_title(self, text: str, etype: EbookType) -> str:
        book_type_msg = "a PDF" if etype == EbookType.PDF else "an ePub"
        prompt = PROMPT_TEMPLATE.format(book_type_msg, text)
        try:
            response = self.client.chat.completions.create(
                model="deepseek-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=False,
            )
            if not response.choices:
                raise RuntimeError("LLM returned no choices")

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise RuntimeError("LLM returned empty content")

            ans = content.strip()
            logger.debug("Response from LLM: %s", ans)
            return ans
        except openai.APIError as ex:
            logger.exception("LLM API request failed: %s", ex)
            raise
