import unittest

from jobpilot.schemas.jobs import JobDescription, parse_job_description


class JobDescriptionParserTests(unittest.TestCase):
    def test_parse_job_description_returns_validated_structure(self):
        raw = """
        AI Engineer

        We are hiring an AI Engineer to design and deploy LLM-powered applications.
        Requirements:
        - 3+ years of Python experience
        - Experience with PyTorch, LangChain, and RAG systems
        - Strong understanding of vector databases and prompt engineering

        Responsibilities:
        - Build LLM applications and AI workflows
        - Evaluate and productionize models with MLflow and Azure OpenAI

        Location: Remote, US
        Employment Type: Full-time
        Salary: $150,000 - $200,000
        """

        parsed = parse_job_description(raw)

        self.assertIsInstance(parsed, JobDescription)
        self.assertEqual(parsed.title, "AI Engineer")
        self.assertEqual(parsed.employment_type, "Full-time")
        self.assertEqual(parsed.location, "Remote, US")
        self.assertIn("llm", " ".join(parsed.responsibilities).lower())
        self.assertIn("python", " ".join(parsed.requirements).lower())
        self.assertIn("pytorch", " ".join(parsed.tech_stack).lower())
        self.assertIn("langchain", " ".join(parsed.tech_stack).lower())
        self.assertIn("rag", " ".join(parsed.tech_stack).lower())
        self.assertEqual(parsed.salary_range, "$150,000 - $200,000")


if __name__ == "__main__":
    unittest.main()
