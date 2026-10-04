import json
import uuid
from pathlib import Path

from jobpilot.chains.job_analysis import compare_resume_to_job, extract_important_topics
from jobpilot.chains.job_parser import JobParser
from jobpilot.schemas.jobs import parse_job_description
from jobpilot.tools.web_search import extract_job_page


class JobService:

    def __init__(self, parser: JobParser | None = None):
        self.parser = parser

        self.jobs_dir = Path("data/jobs")
        self.jobs_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def process_job_description(
        self,
        raw_job_description: str,
        resume_text: str | None = None,
        source_url: str | None = None,
        source_title: str | None = None,
    ) -> dict:

        job, parse_method = self._parse(
            raw_job_description
        )

        job_id = str(uuid.uuid4())
        important_topics = extract_important_topics(job, raw_job_description)

        result = {
            "job_id": job_id,
            "raw": raw_job_description,
            "parsed": job.model_dump(),
            "important_topics": important_topics,
            "parse_method": parse_method,
        }

        if source_url or source_title:
            result["source"] = {
                "url": source_url,
                "title": source_title,
            }

        if resume_text:
            result["match"] = compare_resume_to_job(
                job,
                raw_job_description,
                resume_text,
            )

        self._save_result(job_id, result)

        return result

    def process_job_link(
        self,
        job_link: str,
        resume_text: str | None = None,
    ) -> dict:
        job_page = extract_job_page(job_link)
        result = self.process_job_description(
            job_page.text,
            resume_text=resume_text,
            source_url=job_page.url,
            source_title=job_page.title,
        )
        result["source"]["extracted_character_count"] = len(job_page.text)
        return result

    def _parse(self, raw_job_description: str):
        try:
            if self.parser is None:
                self.parser = JobParser()

            return self.parser.parse(raw_job_description), "llm"
        except Exception:
            return parse_job_description(raw_job_description), "fallback"

    def _save_result(self, job_id: str, result: dict) -> None:
        output_path = self.jobs_dir / f"{job_id}.json"

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=2,
                ensure_ascii=False
            )
