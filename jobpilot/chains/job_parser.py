from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter

from jobpilot.schemas.jobs import JobDescription
import os

class JobParser:
    def __init__(self, model_name: str = os.getenv("LLM_MODEL")):
        self.llm = ChatOpenRouter(
            model=model_name,
            temperature=0,
        )

        self.structured_llm = self.llm.with_structured_output(
            JobDescription
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are an expert job description extraction system.

Your task is to analyze a raw job description and convert it
into a structured JobDescription object.

IMPORTANT RULES:

1. Never invent information.
2. Only extract information explicitly present in the job description.
3. If information is unavailable, return null or an empty list.
4. Distinguish required skills from preferred skills.
5. Do not put education requirements inside required_skills.
6. Do not put years of experience inside required_skills.
7. responsibilities must contain actual duties the candidate is expected to perform.
8. required_skills must contain actual skills, technologies, tools, frameworks,
   programming languages, methodologies, or domain skills explicitly required.
9. preferred_skills must contain skills described as preferred, optional,
   bonus, nice-to-have, or desirable.
10. education must contain degree or academic requirements.
11. qualifications should contain other relevant requirements such as
    certifications, communication skills, domain knowledge, etc.
12. tech_stack should contain technologies, frameworks, libraries,
    databases, cloud platforms, and development tools.
13. keywords should contain high-signal concepts that would be useful
    when comparing this job against a candidate's resume.
14. Preserve the meaning of the original job description.
15. Do not infer that a candidate must know a technology merely because
    it is commonly associated with another technology.

Return only the structured JobDescription object.
"""
                ),
                (
                    "human",
                    """
Extract the structured job information from the following job description:

--- JOB DESCRIPTION ---

{job_description}

--- END JOB DESCRIPTION ---
"""
                ),
            ]
        )

        self.chain = self.prompt | self.structured_llm

    def parse(self, job_description: str) -> JobDescription:
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        result = self.chain.invoke(
            {
                "job_description": job_description.strip()
            }
        )

        return result