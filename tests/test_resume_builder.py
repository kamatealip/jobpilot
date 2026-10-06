import unittest
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from jobpilot.services.resume_builder import WORD_NS, build_tailored_resume


class ResumeBuilderTests(unittest.TestCase):
    def test_docx_highlights_matched_topics_and_preserves_resume_details(self):
        resume_text = (
            "Alex Morgan\n"
            "alex@example.com | (555) 123-4567\n"
            "Experience\nBuilt Python services and AWS integrations."
        )
        document_bytes = build_tailored_resume(
            resume_text,
            "Backend Engineer",
            [{"name": "Python"}, {"name": "AWS"}],
        )

        with ZipFile(BytesIO(document_bytes)) as archive:
            self.assertIn("word/document.xml", archive.namelist())
            root = ET.fromstring(archive.read("word/document.xml"))

        paragraphs = [
            "".join(node.text or "" for node in paragraph.findall(".//w:t", {"w": WORD_NS}))
            for paragraph in root.findall(".//w:p", {"w": WORD_NS})
        ]
        document_text = "\n".join(paragraphs)

        self.assertIn("Resume tailored for Backend Engineer", document_text)
        self.assertIn("Python | AWS", document_text)
        self.assertIn(resume_text, document_text)


if __name__ == "__main__":
    unittest.main()