#! /usr/bin/env python3
import logging
import re
import sys
from pathlib import Path

import pypdf

# Releases
kVersions = [
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

# Special characters
kEmDash = chr(0x2014)


def error(*args, **kwargs):
    logging.error(*args, **kwargs)


def info(*args, **kwargs):
    logging.info(*args, **kwargs)


def warning(*args, **kwargs):
    logging.warning(*args, **kwargs)


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


kSuffixMap = {f".{w}.Edition": f".{ordinal(i + 1)}" for i, w in enumerate(kVersions)}


def sanitize_name(s: str):
    # NOTE(storypku): "c++" to "cpp"
    s = (
        re.sub(r"\s*\([^()]*\)", "", s)
        .strip()
        .replace("++", "pp")
        .replace("-", " ")
        .replace(",", " ")
        .replace(":", " ")
    )
    if kEmDash in s:
        s = s.replace(kEmDash, " ")
    s = re.sub(" +", ".", s.strip())
    if s.endswith(".Edition"):
        for k, v in kSuffixMap.items():
            if s.endswith(k):
                s = s[: -len(k)] + v
                break
    return s


def _append_year(title, date_modified, date_created):
    if date_modified:
        title += ".{}".format(date_modified.strftime("%Y"))
    elif date_created:
        title += ".{}".format(date_created.strftime("%Y"))
    return title


def pdf_title_from_doc_info(docinfo):
    title = sanitize_name(docinfo.title)
    return _append_year(title, docinfo.modification_date, docinfo.creation_date)


def pdf_title_from_xmp_info(xmpinfo):
    dc_title = xmpinfo.dc_title.get("x-default", "")
    title = sanitize_name(" ".join(w.capitalize() for w in dc_title.split()))
    return _append_year(title, xmpinfo.xmp_modify_date, xmpinfo.xmp_create_date)


def parse_year_of_book(di, xi):
    if di and xi:
        timestamp = (
            di.modification_date
            or xi.xmp_modify_date
            or di.creation_date
            or xi.xmp_create_date
        )
    elif di:
        timestamp = di.modification_date or di.creation_date
    elif xi:
        timestamp = xi.xmp_modify_date or xi.xmp_create_date
    else:
        return "0000"
    return timestamp.strftime("%Y")


def suggest_title(fpath: Path, year: str):
    return f"{fpath.stem}.{year}"


def rename_pdf(fpath: Path):
    reader = pypdf.PdfReader(fpath)
    doc_info = reader.metadata
    xmp_info = reader.xmp_metadata
    if doc_info and xmp_info:
        warning(f"{fpath}:")
        warning("\tTitle vs DcTitle: ")
        warning(doc_info.title)
        warning(xmp_info.dc_title)

    if doc_info and doc_info.title:
        title = pdf_title_from_doc_info(doc_info)
        info(f'Title of "{fpath}" should be {title}')
    elif xmp_info and xmp_info.dc_title:
        title = pdf_title_from_xmp_info(xmp_info)
        info(f'Title of "{fpath}" should be {title}')
    else:
        year = parse_year_of_book(doc_info, xmp_info)
        title = suggest_title(fpath, year)
        warning(f"Title not found from metadata, suggested=[{title}]")


def rename_epub(fpath: Path):
    pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) != 2:
        error(f"Usage: {sys.argv[0]} <path/to/ebook>")
        sys.exit(0)

    fpath = Path(sys.argv[1])
    if not fpath.exists():
        error(f"Non-exist file: {fpath}")
        sys.exit(1)
    suffix = fpath.suffix
    if suffix == ".pdf":
        rename_pdf(fpath)
    elif suffix == ".epub":
        rename_epub(fpath)
    else:
        error(f"{fpath}: unknown suffix {suffix}")
        sys.exit(1)
