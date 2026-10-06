# JobPilot

JobPilot is a Flask-based resume and job-description matching application. It
accepts a resume upload and either a pasted job description or a public job
posting link, extracts the important job topics, compares them against the
resume, and returns a match score with matched and missing topics.

The project is built around a practical job-search workflow: quickly understand
how well a resume fits a role, identify gaps, and prepare for resume tailoring.

## What This Project Does

JobPilot performs four main actions:

1. Loads a candidate resume from PDF, DOCX, TXT, Markdown, or CSV.
2. Fetches a public job link and extracts readable job-description text.
3. Parses the job description into structured fields such as title, company,
   location, required skills, preferred skills, tech stack, education, and
   keywords.
4. Compares the extracted job topics against the resume and shows a weighted
   resume match score.
5. Generates a downloadable Word resume that highlights job skills verified in
   the uploaded resume while preserving its complete extracted content.

The current app supports both pasted job descriptions and job links. For job
links, it fetches the page, removes low-value HTML content, extracts the likely
job-description text, parses topics, and compares those topics with the
provided resume.

## Key Features

- Resume upload support for `.pdf`, `.docx`, `.txt`, `.md`, and `.csv`.
- Public job-link extraction using a lightweight HTML parser.
- Structured job-description parsing using Google Gemini through LangChain.
- Local fallback parser when the LLM parser is unavailable.
- Important topic extraction from required skills, tech stack, keywords,
  qualifications, education, and preferred skills.
- Weighted resume match score.
- Matched-topic and missing-topic lists for explainability.
- Downloadable tailored `.docx` with verified matching skills highlighted and
  original resume details preserved.
- Chroma vector-store creation for uploaded resumes.
- Unit tests for parsing, vector-store behavior, web extraction, and matching.

## Application Flow

```text
Resume upload
  -> load resume text
  -> split resume into chunks
  -> optionally store chunks in Chroma

Job link or pasted JD
  -> fetch/extract readable JD text
  -> parse structured job information
  -> extract important topics
  -> compare topics with resume text
  -> show match score and gaps
  -> offer a tailored DOCX download when a resume is uploaded
```

## Tech Stack

- Python 3.13+
- Flask
- Flask-WTF
- LangChain
- LangChain Google GenAI
- Chroma
- Pydantic
- PyPDF
- unittest

## Setup

Create and activate the virtual environment, then install dependencies with
your preferred Python package manager. This project already includes `uv.lock`,
so `uv` is a good fit.

```bash
uv sync
```

Create a `.env` file with:

```bash
GOOGLE_API_KEY=your_google_api_key
```

Run the app:

```bash
.venv/bin/flask --app main run --host 127.0.0.1 --port 5001
```

Open:

```text
http://127.0.0.1:5001
```

## Running Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Current test coverage includes:

- Job-description fallback parsing.
- Resume vector-store upsert behavior.
- Important topic extraction.
- Resume-to-job match scoring.
- HTML extraction from job pages.

## Metrics of the Application

The most important metrics for JobPilot fall into four groups: latency,
matching quality, extraction quality, and reliability.

### 1. Latency Metrics

These measure how fast the app responds.

| Metric                     | What It Measures                           | Why It Matters                    |
| -------------------------- | ------------------------------------------ | --------------------------------- |
| Total request latency      | Time from form submit to rendered result   | Main user experience metric       |
| Job page fetch latency     | Time to download the job link HTML         | Depends on external websites      |
| HTML extraction latency    | Time to clean and extract readable JD text | Should stay very low              |
| LLM parse latency          | Time spent parsing the JD with Gemini      | Usually the largest variable cost |
| Resume load latency        | Time to read PDF/DOCX/TXT resume text      | Impacts upload experience         |
| Resume chunking latency    | Time to split resume into chunks           | Should be small                   |
| Embedding latency          | Time to generate vector embeddings         | Can be slow and API-dependent     |
| Vector-store write latency | Time to write resume chunks into Chroma    | Useful for RAG scalability        |
| Match-score latency        | Time to compare topics with resume text    | Should be very low                |

### 2. Matching Quality Metrics

These measure whether the score is useful.

| Metric                   | What It Measures                                  | Target                        |
| ------------------------ | ------------------------------------------------- | ----------------------------- |
| Match score              | Weighted percentage of JD topics found in resume  | Higher is better              |
| Matched topic count      | Number of important topics found in resume        | Higher is better              |
| Missing topic count      | Number of important topics not found              | Lower is better               |
| Required-skill coverage  | Required skills matched / total required skills   | Very important                |
| Tech-stack coverage      | Tech topics matched / total tech topics           | Important for technical roles |
| Preferred-skill coverage | Preferred skills matched / total preferred skills | Useful but lower priority     |

### 3. Extraction Quality Metrics

These measure how well the app understands a job page.

| Metric                   | What It Measures                                     | Why It Matters                      |
| ------------------------ | ---------------------------------------------------- | ----------------------------------- |
| Extracted JD length      | Character count after cleaning page HTML             | Detects empty or noisy extraction   |
| Topic count              | Number of important topics found                     | Detects weak parsing                |
| Required skill precision | Whether extracted required skills are truly required | Prevents inflated scores            |
| Missing field rate       | Empty company, title, location, salary, etc.         | Shows parser quality                |
| Fallback parse rate      | How often the app uses local fallback parsing        | High rate may signal LLM/API issues |

### 4. Reliability Metrics

These measure whether the system works consistently.

| Metric                      | What It Measures                                            |
| --------------------------- | ----------------------------------------------------------- |
| Job-link fetch failure rate | Percentage of links that cannot be fetched                  |
| Unsupported page rate       | Pages blocked by login, bot checks, or JavaScript rendering |
| Resume parsing failure rate | Failed resume loads by file type                            |
| LLM error rate              | Failed structured parsing requests                          |
| Vector-store error rate     | Failed embedding or Chroma writes                           |
| Test pass rate              | Percentage of unit tests passing                            |

## Latency Testing Plan

For each test run, record these timestamps:

```text
request_start
resume_loaded
resume_chunked
vector_store_finished
job_page_fetched
job_text_extracted
job_parsed
match_score_computed
response_rendered
```

From those timestamps, calculate:

```text
total_latency = response_rendered - request_start
resume_latency = resume_loaded - request_start
vector_latency = vector_store_finished - resume_chunked
fetch_latency = job_page_fetched - request_start
extraction_latency = job_text_extracted - job_page_fetched
parse_latency = job_parsed - job_text_extracted
matching_latency = match_score_computed - job_parsed
```

Recommended latency targets for a good local development experience:

| Operation                     | Good Target |
| ----------------------------- | ----------- |
| HTML extraction               | < 200 ms    |
| Match scoring                 | < 100 ms    |
| Resume TXT/DOCX loading       | < 500 ms    |
| Resume PDF loading            | < 2 s       |
| Job page fetch                | < 3 s       |
| LLM parsing                   | < 8 s       |
| Full resume + job-link result | < 12 s      |

## Measured Latency Baseline

Measured on October 4, 2026 with:

```bash
.venv/bin/python scripts/measure_latency.py --iterations 100 --warmups 10 --json
```

This benchmark measures the local, no-external-API path. It uses a synthetic
resume and synthetic job HTML so the result is repeatable and does not depend on
Google API latency, embedding latency, or public job-board network behavior.

| Stage                     |      p50 |  Average |      p95 |      Max |
| ------------------------- | -------: | -------: | -------: | -------: |
| Resume TXT load           | 0.042 ms | 0.058 ms | 0.129 ms | 0.155 ms |
| Resume split              | 0.027 ms | 0.031 ms | 0.053 ms | 0.056 ms |
| HTML text extraction      | 0.394 ms | 0.434 ms | 0.653 ms | 0.764 ms |
| Fallback JD parse         | 0.283 ms | 0.316 ms | 0.491 ms | 0.511 ms |
| Topic extraction          | 0.120 ms | 0.134 ms | 0.216 ms | 0.244 ms |
| Match scoring             | 0.290 ms | 0.321 ms | 0.486 ms | 0.572 ms |
| End-to-end local pipeline | 1.165 ms | 1.297 ms | 2.010 ms | 2.193 ms |

The same benchmark also measured existing local PDF resume loading without
printing any resume content:

| PDF Samples | Failures |        p50 |   Average |        p95 |        Max |
| ----------: | -------: | ---------: | --------: | ---------: | ---------: |
|           3 |        0 | 105.329 ms | 94.498 ms | 152.339 ms | 152.339 ms |

The benchmark sample produced a `78%` match score by matching `10` of `13`
important job topics. This score is only a sample sanity check, not a claim
about real-world matching accuracy.

Not measured in this default benchmark:

- LLM structured parsing latency.
- Google embedding latency.
- External public job-site network latency.
- JavaScript-rendered job-board latency.

These unmeasured parts are expected to dominate real-world latency. The local
matching logic itself is already fast; the main production latency risk is from
network calls, LLM parsing, embeddings, and blocked or JavaScript-heavy job
boards.

## Best Metrics to Prioritize

The most valuable metrics to track first are:

1. Total request latency.
2. LLM parse latency.
3. Job-link fetch failure rate.
4. Required-skill coverage.
5. Match score.
6. Missing topic count.
7. Fallback parse rate.
8. Test pass rate.

These give the clearest picture of user experience, application reliability, and
match quality.

## How Much of the Actual Problem Is Solved

The actual product problem is:

```text
Given a resume and a job link, extract the JD, understand the important topics,
compare them with the resume, and show a useful match score with evidence.
```

Current status: JobPilot has a working MVP for this workflow. The core local
pipeline is implemented and fast, but production-grade accuracy and reliability
still need work.

| Problem Area                      | Current Status                                                                                                                | Estimated Solved |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------: |
| Resume upload and text extraction | Works for PDF, DOCX, TXT, Markdown, and CSV. Needs better handling for scanned PDFs and unusual layouts.                      |              80% |
| Job-link extraction               | Works for normal public HTML pages. Needs browser rendering for JavaScript-heavy or blocked job boards.                       |              65% |
| JD parsing and topic extraction   | Works with Gemini structured parsing and a local fallback parser. Needs stronger validation and confidence scores.            |              70% |
| Resume-to-JD match score          | Working weighted topic score with matched and missing topics. Needs semantic matching and calibration against real examples.  |              60% |
| Result explainability             | Shows score, important topics, matched topics, and missing topics. Needs tailoring suggestions.                               |              75% |
| Latency testing                   | Repeatable local benchmark exists. Needs in-app timing logs for real user requests.                                           |              50% |
| Production reliability            | Handles the happy path and some fallback cases. Needs caching, retries, better error states, and job-board-specific handling. |              45% |

Overall estimate:

| Level                           | Estimate |
| ------------------------------- | -------: |
| MVP workflow solved             |      70% |
| Production-grade problem solved |      45% |

The biggest solved part is the core workflow: upload resume, provide JD/link,
extract topics, compare, and show a score. The biggest unsolved part is robust
real-world behavior across many job boards and better semantic matching.

## What Can Be Improved

- Add built-in timing instrumentation around every pipeline step.
- Store latency records in JSON or SQLite for comparison across test runs.
- Add semantic matching with embeddings instead of only keyword/topic matching.
- Use the existing Chroma vector store for deeper resume-to-JD retrieval.
- Add support for JavaScript-rendered job boards using a browser renderer.
- Cache fetched job pages and parsed job descriptions by URL.
- Improve the fallback parser for messy job descriptions.
- Add confidence scores for extracted fields and topics.
- Show resume-tailoring suggestions, not only missing topics.
- Add integration tests with sample resumes and sample job pages.
- Add UI states for loading, partial extraction, blocked links, and parser fallback.
- Move secret keys and Flask config into environment-based settings.

## Current Limitations

- Some job boards block automated fetching or require login.
- JavaScript-heavy pages may not expose the full job description in raw HTML.
- The current match score is topic based, so it may miss semantic matches with
  different wording.
- LLM parsing depends on `GOOGLE_API_KEY` and external API latency.
- Vector-store creation can fail independently of local match scoring if
  embeddings are unavailable.

## Project Goal

The goal of JobPilot is to help candidates quickly answer:

```text
How well does my resume match this job?
What important skills or topics are missing?
What should I tailor before applying?
```

The current implementation already supports the first version of that workflow:
upload a resume, provide a job link, and receive a match score with clear topic
evidence.
