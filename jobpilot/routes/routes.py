from pathlib import Path

from flask import abort, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from jobpilot import app
from jobpilot.forms.chat_form import ChatForm
from jobpilot.rag.loader import documents_to_text, load_resume
from jobpilot.rag.splitter import split_resume
from jobpilot.rag.vectorstore import build_vector_store
from jobpilot.services.job_services import JobService
from jobpilot.services.resume_builder import build_tailored_resume


@app.route("/", methods=["GET", "POST"])
def home():
    form = ChatForm()
    error = None

    if request.method == "POST" and form.validate_on_submit():
        uploaded_file = form.file.data
        job_description = (form.job_description.data or "").strip()
        job_link = (form.job_link.data or "").strip()
        resume_text = None
        uploaded_filename = None
        chunk_count = None
        collection_name = None
        vector_store_ready = False
        vector_store_error = None

        if uploaded_file and uploaded_file.filename:
            uploaded_filename = secure_filename(uploaded_file.filename)
            upload_dir = Path(app.root_path) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / uploaded_filename
            uploaded_file.save(file_path)

            try:
                raw_documents = load_resume(str(file_path))
                chunks = split_resume(raw_documents)
                resume_text = documents_to_text(raw_documents)
                chunk_count = len(chunks)
            except Exception as exc:
                error = str(exc)

            if not error and chunks:
                vector_dir = Path(app.root_path) / "data" / "vectorstore"
                vector_dir.mkdir(parents=True, exist_ok=True)
                collection_name = f"jobpilot_{Path(uploaded_filename).stem.lower()}"

                try:
                    vector_store = build_vector_store(chunks, str(vector_dir), collection_name)
                    vector_store_ready = vector_store is not None
                except Exception as exc:
                    vector_store_error = str(exc)

        if error:
            return render_template(
                "home.html",
                form=form,
                submitted=False,
                error=error,
            )

        try:
            service = JobService()

            if job_link:
                result = service.process_job_link(
                    job_link,
                    resume_text=resume_text,
                )
            elif job_description:
                result = service.process_job_description(
                    job_description,
                    resume_text=resume_text,
                )
            else:
                result = None

            if resume_text and result and result.get("match"):
                generated_dir = Path(app.root_path) / "uploads" / "tailored_resumes"
                generated_dir.mkdir(parents=True, exist_ok=True)
                document_path = generated_dir / f"{result['job_id']}.docx"
                document_path.write_bytes(
                    build_tailored_resume(
                        resume_text,
                        result["parsed"].get("title", "the target role"),
                        result["match"].get("matched_topics", []),
                    )
                )
                result["tailored_resume_url"] = url_for(
                    "download_tailored_resume",
                    job_id=result["job_id"],
                )

            return render_template(
                "home.html",
                form=form,
                submitted=True,
                result=result,
                uploaded_file=uploaded_filename,
                chunk_count=chunk_count,
                collection_name=collection_name,
                vector_store_ready=vector_store_ready,
                vector_store_error=vector_store_error,
            )
        except Exception as exc:
            error = str(exc)

    return render_template(
        "home.html",
        form=form,
        submitted=False,
        error=error,
    )


@app.get("/resume/<uuid:job_id>/download")
def download_tailored_resume(job_id):
    document_path = (
        Path(app.root_path)
        / "uploads"
        / "tailored_resumes"
        / f"{job_id}.docx"
    )
    if not document_path.is_file():
        abort(404)

    return send_file(
        document_path,
        as_attachment=True,
        download_name="tailored_resume.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
