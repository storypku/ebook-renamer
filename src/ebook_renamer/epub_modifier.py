#!/usr/bin/env python3

import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def change_epub_title(fpath: Path, new_title: str) -> None:
    with zipfile.ZipFile(fpath, "r") as src:
        container = ET.fromstring(src.read("META-INF/container.xml"))

        rootfile = container.find("container:rootfiles/container:rootfile", NS)
        if rootfile is None:
            raise ValueError("EPUB package document not found")

        opf_path = rootfile.attrib["full-path"]

        opf = ET.fromstring(src.read(opf_path))

        metadata = opf.find("opf:metadata", NS)
        if metadata is None:
            raise ValueError("EPUB metadata not found")

        # Remove all existing dc:title elements.
        for elem in metadata.findall("dc:title", NS):
            metadata.remove(elem)

        # Add exactly one new title.
        ET.SubElement(
            metadata,
            f"{{{NS['dc']}}}title",
        ).text = new_title

        # Preserve the original namespace prefixes where possible.
        ET.register_namespace("", NS["opf"])
        ET.register_namespace("dc", NS["dc"])

        updated_opf = ET.tostring(
            opf,
            encoding="utf-8",
            xml_declaration=True,
        )

        # Write a temporary EPUB to avoid corrupting the original.
        with tempfile.NamedTemporaryFile(
            dir=fpath.parent,
            suffix=".epub",
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)

            try:
                with zipfile.ZipFile(tmp_path, "w") as dst:
                    for item in src.infolist():
                        data = (
                            updated_opf
                            if item.filename == opf_path
                            else src.read(item.filename)
                        )
                        dst.writestr(item, data)

                tmp_path.replace(fpath)

            except Exception:
                tmp_path.unlink(missing_ok=True)
                raise


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <path/to/epub> <new_title>", file=sys.stderr)
        sys.exit(1)

    fpath = Path(sys.argv[1])
    if not fpath.is_file():
        print(f"File not found: {fpath}", file=sys.stderr)
        sys.exit(1)

    try:
        change_epub_title(fpath, sys.argv[2])
    except Exception as ex:
        print(f"Failed to change title of ebook: {ex}", file=sys.stderr)
        sys.exit(1)
