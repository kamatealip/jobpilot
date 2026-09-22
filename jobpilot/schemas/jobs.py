from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    title: str = Field(..., description="The title of the job")

    company: str | None = Field(default=None,
    description=
    "Company or employer name if explicitly mentioned")

    location: str | None = Field(
        default=None,
        description="Job location or remote/huybrid arrangement if mentioned."
    )

    employement_type: str | None = Field(
        default=None,
        description="Employement type such as Full-time, Part-time, Contract or Internship"
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
