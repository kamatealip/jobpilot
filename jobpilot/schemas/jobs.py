import re

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class JobDescription(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., description="The title of the job")

    company: str | None = Field(default=None,
    description=
    "Company or employer name if explicitly mentioned")

    location: str | None = Field(
        default=None,
        description="Job location or remote/huybrid arrangement if mentioned."
    )

    employment_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("employment_type", "employement_type"),
        description="Employment type such as Full-time, Part-time, Contract or Internship"
    )

    salary_range: str | None = Field(
        default=None,
        description="Salary or Compensation range if explicitly mentioned"
    )

    summary: str | None = Field(
        default=None,
        description="concise summary of the role and its purpose."
    )

    responsibilities: list[str] | None = Field(
        default=None,
        description="specific responsibilities and duties of the candidate"
    )

    required_skills: list[str] | None = Field(
        default=None,
        description="Skills explicitly required for the role."
    )

    preferred_skills: list[str] | None = Field(
        default_factory=list,
        description=" Optional, preferred, or nice-to-have skills."
    )

    experience: str | None = Field(
        default=None,
        description="Required professional experience, such as '2+ years'."
    )

    education: list[str] = Field(
           default_factory=list,
           description="Required or preferred educational qualifications."
       )

    qualifications: list[str] = Field(
           default_factory=list,
           description="Other qualifications, certifications, domain knowledge, or soft-skill requirements."
       )

    tech_stack: list[str] = Field(
           default_factory=list,
           description="Technologies, frameworks, libraries, platforms, databases, and tools mentioned."
       )

    keywords: list[str] = Field(
           default_factory=list,
           description="High-signal concepts and phrases useful for resume/job matching."
       )

    @property
    def employement_type(self) -> str | None:
        return self.employment_type

    @property
    def requirements(self) -> list[str]:
        return self.required_skills or []


SECTION_HEADINGS = {
    "requirements",
    "responsibilities",
    "preferred qualifications",
    "qualifications",
    "skills",
    "education",
    "about the role",
    "about us",
}

KNOWN_TECH_TERMS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "fastapi",
    "flask",
    "django",
    "react",
    "node",
    "langchain",
    "langgraph",
    "rag",
    "llm",
    "pytorch",
    "tensorflow",
    "mlflow",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "azure openai",
    "vector databases",
    "prompt engineering",
]


def parse_job_description(raw_job_description: str) -> JobDescription:
    """Parse a simple job description without calling an LLM.

    This is intentionally conservative and is used by tests and as a fallback
    when the structured LLM parser is unavailable.
    """
    if not raw_job_description or not raw_job_description.strip():
        raise ValueError("Job description is required")

    text = raw_job_description.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    title = _first_non_label_line(lines) or "Unknown role"
    responsibilities = _extract_bullets(lines, "responsibilities")
    required_skills = _extract_bullets(lines, "requirements")
    preferred_skills = _extract_bullets(lines, "preferred qualifications")
    education = [
        item for item in required_skills + preferred_skills
        if re.search(r"\b(degree|bachelor|master|phd|university|college)\b", item, re.I)
    ]
    required_skills = [item for item in required_skills if item not in education]
    tech_stack = _extract_tech_stack(text)

    return JobDescription(
        title=title,
        company=_extract_label(text, "Company"),
        location=_extract_label(text, "Location"),
        employment_type=_extract_label(text, "Employment Type"),
        salary_range=_extract_label(text, "Salary"),
        summary=_first_sentence(text),
        responsibilities=responsibilities,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        education=education,
        qualifications=[],
        tech_stack=tech_stack,
        keywords=tech_stack[:],
    )


def _first_non_label_line(lines: list[str]) -> str | None:
    for line in lines:
        if ":" not in line and not line.startswith("-"):
            return line
    return lines[0] if lines else None


def _extract_label(text: str, label: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+)$", text, re.I | re.M)
    return match.group(1).strip() if match else None


def _extract_bullets(lines: list[str], heading: str) -> list[str]:
    items: list[str] = []
    in_section = False

    for line in lines:
        normalized = line.rstrip(":").strip().lower()
        if normalized == heading:
            in_section = True
            continue
        if in_section and (normalized in SECTION_HEADINGS or re.match(r"^[a-z ]+:\s+.+", line, re.I)):
            break
        if in_section:
            cleaned = re.sub(r"^[-*]\s*", "", line).strip()
            if cleaned:
                items.append(cleaned)

    return items


def _extract_tech_stack(text: str) -> list[str]:
    lower_text = text.lower()
    found = []

    for term in KNOWN_TECH_TERMS:
        pattern = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, lower_text):
            found.append(term.upper() if term in {"rag", "llm", "aws", "gcp"} else term.title())

    return found


def _first_sentence(text: str) -> str | None:
    compact = re.sub(r"\s+", " ", text).strip()
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    return match.group(1).strip() if match else compact[:240]
