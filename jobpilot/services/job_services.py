import json
import uuid
from pathlib import Path

from jobpilot.chains.job_parser import JobParser


class JobService:

    def __init__(self):
        self.parser = JobParser()

        self.jobs_dir = Path("data/jobs")
        self.jobs_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def process_job_description(
        self,
        raw_job_description: str
    ) -> dict:

        job = self.parser.parse(
            raw_job_description
        )

        job_id = str(uuid.uuid4())

        result = {
            "job_id": job_id,
            "raw": raw_job_description,
            "parsed": job.model_dump()
        }

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

        return result