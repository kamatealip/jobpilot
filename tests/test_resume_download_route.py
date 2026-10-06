import unittest
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from zipfile import ZipFile

from jobpilot import app


class ResumeDownloadRouteTests(unittest.TestCase):
    def setUp(self):
        self.original_testing = app.config.get("TESTING")
        self.original_csrf = app.config.get("WTF_CSRF_ENABLED")
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()

    def tearDown(self):
        app.config["TESTING"] = self.original_testing
        app.config["WTF_CSRF_ENABLED"] = self.original_csrf

    def test_upload_renders_and_serves_tailored_resume(self):
        job_id = str(uuid4())
        upload_name = f"test_resume_{job_id}.txt"
        upload_path = Path(app.root_path) / "uploads" / upload_name
        document_path = (
            Path(app.root_path)
            / "uploads"
            / "tailored_resumes"
            / f"{job_id}.docx"
        )
        self.addCleanup(upload_path.unlink, missing_ok=True)
        self.addCleanup(document_path.unlink, missing_ok=True)
        resume_text = "Alex Morgan\nalex@example.com | (555) 123-4567\nPython developer"
        result = {
            "job_id": job_id,
            "parsed": {"title": "Backend Engineer"},
            "important_topics": [],
            "match": {
                "score": 100,
                "matched_count": 1,
                "topic_count": 1,
                "matched_topics": [{"name": "Python"}],
                "missing_topics": [],
            },
        }

        with (
            patch("jobpilot.routes.routes.load_resume", return_value=[]),
            patch("jobpilot.routes.routes.split_resume", return_value=[]),
            patch("jobpilot.routes.routes.documents_to_text", return_value=resume_text),
            patch("jobpilot.routes.routes.JobService") as job_service,
        ):
            job_service.return_value.process_job_description.return_value = result
            response = self.client.post(
                "/",
                data={
                    "file": (BytesIO(b"source resume"), upload_name),
                    "job_description": "Backend Engineer, Python required",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Download tailored resume (.docx)", response.data)

        download = self.client.get(f"/resume/{job_id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertIn("attachment", download.headers["Content-Disposition"])
        with ZipFile(BytesIO(download.data)) as archive:
            self.assertIn("word/document.xml", archive.namelist())
            self.assertIn("word/styles.xml", archive.namelist())
        download.close()


if __name__ == "__main__":
    unittest.main()