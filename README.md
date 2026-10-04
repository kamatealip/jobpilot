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

| Metric | What It Measures | Why It Matters |
| --- | --- | --- |
| Total request latency | Time from form submit to rendered result | Main user experience metric |
| Job page fetch latency | Time to download the job link HTML | Depends on external websites |
| HTML extraction latency | Time to clean and extract readable JD text | Should stay very low |
| LLM parse latency | Time spent parsing the JD with Gemini | Usually the largest variable cost |
| Resume load latency | Time to read PDF/DOCX/TXT resume text | Impacts upload experience |
| Resume chunking latency | Time to split resume into chunks | Should be small |
| Embedding latency | Time to generate vector embeddings | Can be slow and API-dependent |
| Vector-store write latency | Time to write resume chunks into Chroma | Useful for RAG scalability |
| Match-score latency | Time to compare topics with resume text | Should be very low |

### 2. Matching Quality Metrics

These measure whether the score is useful.

| Metric | What It Measures | Target |
| --- | --- | --- |
| Match score | Weighted percentage of JD topics found in resume | Higher is better |
| Matched topic count | Number of important topics found in resume | Higher is better |
| Missing topic count | Number of important topics not found | Lower is better |
| Required-skill coverage | Required skills matched / total required skills | Very important |
| Tech-stack coverage | Tech topics matched / total tech topics | Important for technical roles |
| Preferred-skill coverage | Preferred skills matched / total preferred skills | Useful but lower priority |

### 3. Extraction Quality Metrics

These measure how well the app understands a job page.

| Metric | What It Measures | Why It Matters |
| --- | --- | --- |
| Extracted JD length | Character count after cleaning page HTML | Detects empty or noisy extraction |
| Topic count | Number of important topics found | Detects weak parsing |
| Required skill precision | Whether extracted required skills are truly required | Prevents inflated scores |
| Missing field rate | Empty company, title, location, salary, etc. | Shows parser quality |
| Fallback parse rate | How often the app uses local fallback parsing | High rate may signal LLM/API issues |

### 4. Reliability Metrics

These measure whether the system works consistently.

| Metric | What It Measures |
| --- | --- |
| Job-link fetch failure rate | Percentage of links that cannot be fetched |
| Unsupported page rate | Pages blocked by login, bot checks, or JavaScript rendering |
| Resume parsing failure rate | Failed resume loads by file type |
| LLM error rate | Failed structured parsing requests |
| Vector-store error rate | Failed embedding or Chroma writes |
| Test pass rate | Percentage of unit tests passing |

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

| Operation | Good Target |
| --- | --- |
| HTML extraction | < 200 ms |
| Match scoring | < 100 ms |
| Resume TXT/DOCX loading | < 500 ms |
| Resume PDF loading | < 2 s |
| Job page fetch | < 3 s |
| LLM parsing | < 8 s |
| Full resume + job-link result | < 12 s |

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
