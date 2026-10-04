from pathlib import Path

from flask import render_template, request
from werkzeug.utils import secure_filename

from jobpilot import app
from jobpilot.forms.chat_form import ChatForm
from jobpilot.rag.loader import documents_to_text, load_resume
from jobpilot.rag.splitter import split_resume
from jobpilot.rag.vectorstore import build_vector_store
from jobpilot.services.job_services import JobService


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
