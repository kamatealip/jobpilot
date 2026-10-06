from __future__ import annotations

from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
ET.register_namespace("w", WORD_NS)
ET.register_namespace("r", REL_NS)


def build_tailored_resume(
    resume_text: str,
    job_title: str,
    matched_topics: list[dict],
) -> bytes:
    """Build a Word document that emphasizes verified skills without inventing facts."""
    document = ET.Element(_tag(WORD_NS, "document"))
    body = ET.SubElement(document, _tag(WORD_NS, "body"))

    _add_paragraph(body, f"Resume tailored for {job_title or 'the target role'}", "Title")
    _add_paragraph(
        body,
        "Relevant skills verified in the uploaded resume",
        "Heading1",
    )

    skill_names = list(dict.fromkeys(topic["name"] for topic in matched_topics))
    if skill_names:
        _add_paragraph(body, " | ".join(skill_names))
    else:
        _add_paragraph(body, "No job-description skills were verified in the uploaded resume.")

    _add_paragraph(body, "Original resume details", "Heading1")
    for line in resume_text.splitlines():
        _add_paragraph(body, line)

    section = ET.SubElement(body, _tag(WORD_NS, "sectPr"))
    page_size = ET.SubElement(section, _tag(WORD_NS, "pgSz"))
    page_size.set(_tag(WORD_NS, "w"), "12240")
    page_size.set(_tag(WORD_NS, "h"), "15840")
    margins = ET.SubElement(section, _tag(WORD_NS, "pgMar"))
    for side in ("top", "right", "bottom", "left"):
        margins.set(_tag(WORD_NS, side), "1080")

    styles = _build_styles()
    content_types = ET.Element(_tag(CONTENT_TYPES_NS, "Types"))
    ET.SubElement(
        content_types,
        _tag(CONTENT_TYPES_NS, "Default"),
        {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"},
    )
    ET.SubElement(
        content_types,
        _tag(CONTENT_TYPES_NS, "Default"),
        {"Extension": "xml", "ContentType": "application/xml"},
    )
    ET.SubElement(
        content_types,
        _tag(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/word/document.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        },
    )
    ET.SubElement(
        content_types,
        _tag(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/word/styles.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
        },
    )

    relationships = ET.Element(_tag(PACKAGE_REL_NS, "Relationships"))
    ET.SubElement(
        relationships,
        _tag(PACKAGE_REL_NS, "Relationship"),
        {
            "Id": "rId1",
            "Type": f"{REL_NS}/officeDocument",
            "Target": "word/document.xml",
        },
    )
    document_relationships = ET.Element(_tag(PACKAGE_REL_NS, "Relationships"))
    ET.SubElement(
        document_relationships,
        _tag(PACKAGE_REL_NS, "Relationship"),
        {
            "Id": "rId1",
            "Type": f"{REL_NS}/styles",
            "Target": "styles.xml",
        },
    )

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xml_bytes(content_types))
        archive.writestr("_rels/.rels", _xml_bytes(relationships))
        archive.writestr("word/document.xml", _xml_bytes(document))
        archive.writestr("word/_rels/document.xml.rels", _xml_bytes(document_relationships))
        archive.writestr("word/styles.xml", _xml_bytes(styles))

    return output.getvalue()


def _build_styles() -> ET.Element:
    styles = ET.Element(_tag(WORD_NS, "styles"))
    _add_style(styles, "Normal", "Aptos", "22", "263238")
    _add_style(styles, "Title", "Aptos Display", "36", "135D66", bold=True)
    _add_style(styles, "Heading1", "Aptos", "26", "135D66", bold=True)
    return styles


def _add_style(
    styles: ET.Element,
    style_id: str,
    font: str,
    size: str,
    color: str,
    bold: bool = False,
) -> None:
    style = ET.SubElement(
        styles,
        _tag(WORD_NS, "style"),
        {_tag(WORD_NS, "type"): "paragraph", _tag(WORD_NS, "styleId"): style_id},
    )
    ET.SubElement(style, _tag(WORD_NS, "name"), {_tag(WORD_NS, "val"): style_id})
    properties = ET.SubElement(style, _tag(WORD_NS, "rPr"))
    ET.SubElement(
        properties,
        _tag(WORD_NS, "rFonts"),
        {
            _tag(WORD_NS, "ascii"): font,
            _tag(WORD_NS, "hAnsi"): font,
        },
    )
    ET.SubElement(properties, _tag(WORD_NS, "sz"), {_tag(WORD_NS, "val"): size})
    ET.SubElement(properties, _tag(WORD_NS, "color"), {_tag(WORD_NS, "val"): color})
    if bold:
        ET.SubElement(properties, _tag(WORD_NS, "b"))


def _add_paragraph(parent: ET.Element, text: str, style: str | None = None) -> None:
    paragraph = ET.SubElement(parent, _tag(WORD_NS, "p"))
    if style:
        properties = ET.SubElement(paragraph, _tag(WORD_NS, "pPr"))
        ET.SubElement(
            properties,
            _tag(WORD_NS, "pStyle"),
            {_tag(WORD_NS, "val"): style},
        )
    if text:
        run = ET.SubElement(paragraph, _tag(WORD_NS, "r"))
        text_node = ET.SubElement(run, _tag(WORD_NS, "t"))
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        text_node.text = text


def _tag(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _xml_bytes(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)