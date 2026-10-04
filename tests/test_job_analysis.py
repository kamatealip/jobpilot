import unittest

from jobpilot.chains.job_analysis import compare_resume_to_job, extract_important_topics
from jobpilot.schemas.jobs import JobDescription


class JobAnalysisTests(unittest.TestCase):
    def test_extract_important_topics_uses_job_fields(self):
        job = JobDescription(
            title="AI Engineer",
            required_skills=["Python", "RAG systems"],
            tech_stack=["LangChain", "Vector databases"],
            keywords=["LLM evaluation"],
        )

        topics = extract_important_topics(job)
        topic_names = [topic["name"] for topic in topics]

        self.assertIn("Python", topic_names)
        self.assertIn("LangChain", topic_names)
        self.assertIn("LLM evaluation", topic_names)

    def test_compare_resume_to_job_returns_weighted_score(self):
        job = JobDescription(
            title="AI Engineer",
            required_skills=["Python", "RAG systems"],
            tech_stack=["LangChain", "Vector databases"],
            preferred_skills=["AWS"],
        )
        resume = "Built Python and LangChain RAG applications with vector databases."

        match = compare_resume_to_job(job, "", resume)

        self.assertGreaterEqual(match["score"], 80)
        self.assertEqual(match["matched_count"], 4)
        self.assertEqual(match["topic_count"], 5)


if __name__ == "__main__":
    unittest.main()
