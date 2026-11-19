#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import pypdf
from openai import OpenAI

MIN_NUMBER_OF_PAGES = 3
MAX_TEXT_LENGTH = 4096

PROMPT_TEMPLATE = """
Below is the text from the first few pages of a PDF.
Please extract the title of this document.

Return only the title text, without any explanation or punctuation.

Text content:
{}
"""


def extract_text_from_first_pages(fpath: Path) -> str:
    """Extract text from the first few pages of a PDF."""
    reader = pypdf.PdfReader(fpath)

    result = []
    for page in reader.pages[:MIN_NUMBER_OF_PAGES]:
        text = page.extract_text()
        if text:
            result.append(text)

    return "".join(result)


class LlmClient:
    """Client for extracting document titles using an LLM."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

    def extract_title(self, text: str) -> str:
        prompt = PROMPT_TEMPLATE.format(text[:MAX_TEXT_LENGTH])

        response = self.client.chat.completions.create(
            model="deepseek-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return response.choices[0].message.content.strip()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pdf-file>", file=sys.stderr)
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.is_file():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    text = extract_text_from_first_pages(pdf_path)

    if not text.strip():
        print("No extractable text found in PDF.", file=sys.stderr)
        sys.exit(1)

    llm = LlmClient()
    title = llm.extract_title(text)

    print(f"Title suggested by LLM: {title}")


if __name__ == "__main__":
    main()

