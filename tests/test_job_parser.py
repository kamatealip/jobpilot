import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to sys.path so jobpilot module can be imported directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from jobpilot.chains.job_parser import JobParser


def main():

    jd = """
    AI Engineer

    Company: Example Technologies
    Location: Bangalore, India
    Employment Type: Full-time

    About the Role:

    We are looking for an AI Engineer to build
    production-grade generative AI applications.

    Responsibilities:

    - Build RAG applications using LangChain.
    - Develop Python APIs using FastAPI.
    - Build and evaluate LLM-based applications.
    - Work with vector databases.

    Requirements:

    - Strong Python programming skills.
    - Experience with LangChain and RAG.
    - Experience building REST APIs.
    - 1-2 years of software development experience.
    - Bachelor's degree in Computer Science or related field.

    Preferred Qualifications:

    - Experience with LangGraph.
    - Experience with AWS.
    - Docker knowledge.
    """

    parser = JobParser()

    result = parser.parse(jd)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
