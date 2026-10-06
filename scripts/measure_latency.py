from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from jobpilot.chains.job_analysis import compare_resume_to_job, extract_important_topics
from jobpilot.rag.loader import documents_to_text, load_resume
from jobpilot.rag.splitter import split_resume
from jobpilot.schemas.jobs import parse_job_description
from jobpilot.tools.web_search import extract_visible_text


SAMPLE_RESUME = """
AI Engineer

Experience
- Built production RAG applications using Python, LangChain, vector databases,
  and prompt engineering.
- Developed FastAPI services for LLM workflows and evaluation pipelines.
- Worked with Docker, AWS, REST APIs, and model monitoring.
- Created resume and job matching tools using embeddings and structured parsing.

Skills
Python, LangChain, RAG, LLM evaluation, vector databases, FastAPI, Flask,
Docker, AWS, REST APIs, prompt engineering, data pipelines.

Education
Bachelor's degree in Computer Science.
"""


SAMPLE_JOB_HTML = """
<!doctype html>
<html>
  <head>
    <title>AI Engineer - Example Technologies</title>
    <script>window.analytics = true;</script>
  </head>
  <body>
    <nav>Sign in</nav>
    <main>
      <h1>AI Engineer</h1>
      <p>Company: Example Technologies</p>
      <p>Location: Remote, US</p>
      <p>Employment Type: Full-time</p>
      <p>Salary: $140,000 - $180,000</p>

      <h2>About the Role</h2>
      <p>
        We are hiring an AI Engineer to build production-grade generative AI
        applications for resume and job matching workflows.
      </p>

      <h2>Responsibilities</h2>
      <ul>
        <li>Build RAG applications using LangChain.</li>
        <li>Develop Python APIs using FastAPI.</li>
        <li>Evaluate LLM-based applications.</li>
        <li>Work with vector databases.</li>
      </ul>

      <h2>Requirements</h2>
      <ul>
        <li>Strong Python programming skills.</li>
        <li>Experience with LangChain and RAG systems.</li>
        <li>Experience building REST APIs.</li>
        <li>2+ years of software development experience.</li>
        <li>Bachelor's degree in Computer Science or related field.</li>
      </ul>

      <h2>Preferred Qualifications</h2>
      <ul>
        <li>Experience with AWS.</li>
        <li>Docker knowledge.</li>
      </ul>
    </main>
  </body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure local JobPilot pipeline latency without external API calls."
    )
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args()

    result = run_benchmark(args.iterations, args.warmups)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)


def run_benchmark(iterations: int, warmups: int) -> dict:
    iterations = max(1, iterations)
    warmups = max(0, warmups)

    with tempfile.TemporaryDirectory(prefix="jobpilot-latency-") as tmpdir:
        resume_path = Path(tmpdir) / "sample_resume.txt"
        resume_path.write_text(SAMPLE_RESUME, encoding="utf-8")

        stage_samples: dict[str, list[float]] = {
            "resume_txt_load": [],
            "resume_split": [],
            "html_text_extraction": [],
            "fallback_job_parse": [],
            "topic_extraction": [],
            "match_scoring": [],
            "end_to_end_local_pipeline": [],
        }
        last_match = None
        last_job_text = ""
        last_resume_text = ""

        for index in range(warmups + iterations):
            collect = index >= warmups
            sample = measure_pipeline_once(resume_path)

            if collect:
                for stage, value in sample["stage_ms"].items():
                    stage_samples[stage].append(value)
                last_match = sample["match"]
                last_job_text = sample["job_text"]
                last_resume_text = sample["resume_text"]

        pdf_result = measure_existing_pdf_loads()

    return {
        "benchmark": "local_no_external_api",
        "iterations": iterations,
        "warmups": warmups,
        "sample": {
            "resume_chars": len(last_resume_text),
            "job_text_chars": len(last_job_text),
        },
        "match_score": last_match["score"] if last_match else None,
        "matched_topics": last_match["matched_count"] if last_match else None,
        "total_topics": last_match["topic_count"] if last_match else None,
        "stages_ms": {
            stage: summarize(samples)
            for stage, samples in stage_samples.items()
        },
        "existing_pdf_resume_load_ms": pdf_result,
        "not_measured_by_default": [
            "LLM structured parsing latency",
            "Google embedding latency",
            "External public job-site network latency",
            "JavaScript-rendered job-board latency",
        ],
    }


def measure_pipeline_once(resume_path: Path) -> dict:
    stage_ms = {}
    total_start = time.perf_counter()

    start = time.perf_counter()
    documents = load_resume(str(resume_path))
    resume_text = documents_to_text(documents)
    stage_ms["resume_txt_load"] = elapsed_ms(start)

    start = time.perf_counter()
    split_resume(documents)
    stage_ms["resume_split"] = elapsed_ms(start)

    start = time.perf_counter()
    job_text = extract_visible_text(SAMPLE_JOB_HTML)
    stage_ms["html_text_extraction"] = elapsed_ms(start)

    start = time.perf_counter()
    job = parse_job_description(job_text)
    stage_ms["fallback_job_parse"] = elapsed_ms(start)

    start = time.perf_counter()
    extract_important_topics(job, job_text)
    stage_ms["topic_extraction"] = elapsed_ms(start)

    start = time.perf_counter()
    match = compare_resume_to_job(job, job_text, resume_text)
    stage_ms["match_scoring"] = elapsed_ms(start)

    stage_ms["end_to_end_local_pipeline"] = elapsed_ms(total_start)

    return {
        "stage_ms": stage_ms,
        "match": match,
        "job_text": job_text,
        "resume_text": resume_text,
    }


def measure_existing_pdf_loads() -> dict:
    upload_dir = Path("jobpilot/uploads")
    pdf_paths = sorted(upload_dir.glob("*.pdf"))
    samples = []
    failures = 0

    for pdf_path in pdf_paths:
        try:
            start = time.perf_counter()
            load_resume(str(pdf_path))
            samples.append(elapsed_ms(start))
        except Exception:
            failures += 1

    summary = summarize(samples) if samples else None
    return {
        "sample_count": len(samples),
        "failure_count": failures,
        "summary": summary,
    }


def summarize(samples: list[float]) -> dict:
    ordered = sorted(samples)
    return {
        "min": round(ordered[0], 3),
        "p50": round(statistics.median(ordered), 3),
        "avg": round(statistics.mean(ordered), 3),
        "p95": round(percentile(ordered, 95), 3),
        "max": round(ordered[-1], 3),
    }


def percentile(ordered: list[float], percentile_value: int) -> float:
    if len(ordered) == 1:
        return ordered[0]
    index = math.ceil((percentile_value / 100) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def print_report(result: dict) -> None:
    print(f"Benchmark: {result['benchmark']}")
    print(f"Iterations: {result['iterations']} warmups: {result['warmups']}")
    print(
        "Sample sizes: "
        f"resume={result['sample']['resume_chars']} chars, "
        f"job={result['sample']['job_text_chars']} chars"
    )
    print(
        "Match: "
        f"{result['match_score']}% "
        f"({result['matched_topics']}/{result['total_topics']} topics)"
    )
    print()
    print("Stage latency, milliseconds")
    for stage, summary in result["stages_ms"].items():
        print(
            f"- {stage}: "
            f"p50={summary['p50']} avg={summary['avg']} "
            f"p95={summary['p95']} max={summary['max']}"
        )

    pdf = result["existing_pdf_resume_load_ms"]
    print()
    print(
        "Existing PDF resume load: "
        f"samples={pdf['sample_count']} failures={pdf['failure_count']}"
    )
    if pdf["summary"]:
        summary = pdf["summary"]
        print(
            f"- p50={summary['p50']} avg={summary['avg']} "
            f"p95={summary['p95']} max={summary['max']}"
        )

    print()
    print("Not measured by default")
    for item in result["not_measured_by_default"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()
