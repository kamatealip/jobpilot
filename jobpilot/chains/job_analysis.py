from __future__ import annotations

import re
from collections.abc import Iterable

from jobpilot.schemas.jobs import JobDescription


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "years",
    "year",
    "experience",
    "strong",
    "knowledge",
    "understanding",
    "ability",
    "skills",
    "skill",
    "using",
    "build",
    "building",
}

TOPIC_FIELDS = [
    ("required_skills", "Required skill", 2.5),
    ("tech_stack", "Technology", 2.2),
    ("keywords", "Keyword", 1.8),
    ("qualifications", "Qualification", 1.5),
    ("education", "Education", 1.2),
    ("preferred_skills", "Preferred skill", 1.0),
]


def extract_important_topics(job: JobDescription, raw_job_description: str = "") -> list[dict]:
    topics: list[dict] = []
    seen: dict[str, int] = {}

    for field_name, category, weight in TOPIC_FIELDS:
        for value in _as_list(getattr(job, field_name, None)):
            _add_topic(topics, seen, value, category, weight)

    if not topics and raw_job_description:
        for value in _fallback_topics(raw_job_description):
            _add_topic(topics, seen, value, "Keyword", 1.0)

    return topics[:30]


def compare_resume_to_job(
    job: JobDescription,
    raw_job_description: str,
    resume_text: str,
) -> dict:
    topics = extract_important_topics(job, raw_job_description)
    if not topics:
        return {
            "score": 0,
            "matched_topics": [],
            "missing_topics": [],
            "topic_count": 0,
            "matched_count": 0,
        }

    normalized_resume = _normalize(resume_text)
    resume_tokens = set(_keyword_tokens(resume_text))

    matched_topics = []
    missing_topics = []
    matched_weight = 0.0
    total_weight = 0.0

    for topic in topics:
        total_weight += topic["weight"]
        if _topic_matches(topic["name"], normalized_resume, resume_tokens):
            matched_topics.append(topic)
            matched_weight += topic["weight"]
        else:
            missing_topics.append(topic)

    score = round((matched_weight / total_weight) * 100) if total_weight else 0

    return {
        "score": score,
        "matched_topics": matched_topics,
        "missing_topics": missing_topics,
        "topic_count": len(topics),
        "matched_count": len(matched_topics),
    }


def _add_topic(
    topics: list[dict],
    seen: dict[str, int],
    value: str,
    category: str,
    weight: float,
) -> None:
    name = _clean_topic(value)
    key = _topic_key(name)

    if not name or len(key) < 2:
        return

    if key in seen:
        index = seen[key]
        if weight > topics[index]["weight"]:
            topics[index]["category"] = category
            topics[index]["weight"] = weight
        return

    seen[key] = len(topics)
    topics.append(
        {
            "name": name,
            "category": category,
            "weight": weight,
        }
    )


def _topic_matches(topic: str, normalized_resume: str, resume_tokens: set[str]) -> bool:
    normalized_topic = _normalize(topic)
    topic_tokens = _keyword_tokens(topic)

    if not topic_tokens:
        return False

    if normalized_topic and normalized_topic in normalized_resume:
        return True

    matched = sum(1 for token in topic_tokens if token in resume_tokens)
    has_matching_acronym = any(
        len(token) <= 4 and token in resume_tokens
        for token in topic_tokens
    )
    if len(topic_tokens) == 1:
        return matched == 1
    if has_matching_acronym:
        return True
    if len(topic_tokens) <= 3:
        return matched == len(topic_tokens)

    return matched / len(topic_tokens) >= 0.7


def _fallback_topics(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[-*•]\s*", "", line).strip()
        if 3 <= len(cleaned) <= 90 and _looks_like_topic(cleaned):
            candidates.append(cleaned)
    return candidates


def _looks_like_topic(value: str) -> bool:
    lowered = value.lower()
    hints = [
        "experience",
        "skill",
        "python",
        "data",
        "cloud",
        "api",
        "model",
        "machine learning",
        "software",
        "database",
    ]
    return any(hint in lowered for hint in hints)


def _as_list(value: Iterable[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item]


def _clean_topic(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value)).strip(" -•\t\r\n")
    value = re.sub(r"\.$", "", value)
    return value


def _topic_key(value: str) -> str:
    return " ".join(_keyword_tokens(value))


def _keyword_tokens(value: str) -> list[str]:
    normalized = _normalize(value)
    tokens = []

    for token in normalized.split():
        if token in STOPWORDS:
            continue
        if len(token) <= 1:
            continue
        tokens.append(_simple_stem(token))

    return tokens


def _normalize(value: str) -> str:
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9+#.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _simple_stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token
