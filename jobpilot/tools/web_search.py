from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ExtractedJobPage:
    url: str
    title: str | None
    text: str


class _ReadableHTMLParser(HTMLParser):
    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "nav",
        "header",
        "footer",
        "form",
    }
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "main",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
        "ol",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self._parts: list[str] = []
        self._title_parts: list[str] = []

    @property
    def title(self) -> str | None:
        title = _compact_whitespace(" ".join(self._title_parts))
        return title or None

    @property
    def text(self) -> str:
        return _clean_extracted_text("\n".join(self._parts))

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return

        text = _compact_whitespace(data)
        if not text:
            return

        if self._in_title:
            self._title_parts.append(text)
            return

        self._parts.append(text)


def extract_job_page(url: str, timeout: int = 15, max_chars: int = 40000) -> ExtractedJobPage:
    _validate_url(url)

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120 Safari/537.36"
            )
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ValueError(f"Unsupported response content type: {content_type}")

            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        raise ValueError(f"Could not fetch job link: HTTP {exc.code}") from exc
    except URLError as exc:
        raise ValueError(f"Could not fetch job link: {exc.reason}") from exc

    parser = _ReadableHTMLParser()
    parser.feed(html)

    page_text = parser.text
    job_text = _focus_job_description(page_text, max_chars=max_chars)
    if not job_text:
        raise ValueError("No readable job description text was found at that link.")

    return ExtractedJobPage(
        url=url,
        title=parser.title,
        text=job_text,
    )


def extract_visible_text(html: str) -> str:
    parser = _ReadableHTMLParser()
    parser.feed(html)
    return parser.text


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please enter a valid HTTP or HTTPS job link.")


def _focus_job_description(text: str, max_chars: int) -> str:
    text = _clean_extracted_text(text)
    if len(text) <= max_chars:
        return text

    marker_pattern = re.compile(
        r"\b(job description|about the role|about this role|responsibilities|"
        r"requirements|qualifications|what you'll do|what you will do|skills)\b",
        re.I,
    )
    match = marker_pattern.search(text)
    if not match:
        return text[:max_chars].strip()

    intro = text[: min(match.start(), 2500)].strip()
    body = text[match.start(): match.start() + max_chars].strip()
    return f"{intro}\n\n{body}".strip()[:max_chars]


def _clean_extracted_text(text: str) -> str:
    text = unescape(text)
    raw_lines = [_compact_whitespace(line) for line in text.splitlines()]
    lines: list[str] = []
    seen: set[str] = set()

    for line in raw_lines:
        if not line or _is_low_value_line(line):
            continue

        key = line.lower()
        if key in seen:
            continue

        seen.add(key)
        lines.append(line)

    return "\n".join(lines).strip()


def _is_low_value_line(line: str) -> bool:
    lowered = line.lower()
    if len(line) <= 2:
        return True

    low_value_phrases = {
        "accept cookies",
        "cookie policy",
        "privacy policy",
        "terms of use",
        "sign in",
        "log in",
        "create alert",
        "share this job",
        "skip to main content",
    }
    return any(phrase in lowered for phrase in low_value_phrases)


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
