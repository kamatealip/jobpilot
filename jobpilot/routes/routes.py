from pathlib import Path

from flask import render_template
from werkzeug.utils import secure_filename

from jobpilot import app
from jobpilot.forms.chat_form import ChatForm
from jobpilot.rag.loader import load_resume
from jobpilot.rag.splitter import split_resume
from jobpilot.rag.vectorstore import build_vector_store


@app.route("/", methods=["GET", "POST"])
def home():
    form = ChatForm()
    error = None

    if form.validate_on_submit():
        uploaded_file = form.file.data

        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            upload_dir = Path(app.root_path) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / filename
            uploaded_file.save(file_path)

            try:
                raw_documents = load_resume(str(file_path))
                chunks = split_resume(raw_documents)

                vector_dir = Path(app.root_path) / "data" / "vectorstore"
                vector_dir.mkdir(parents=True, exist_ok=True)
                collection_name = f"jobpilot_{Path(filename).stem.lower()}"

                vector_store = build_vector_store(chunks, str(vector_dir), collection_name)

                return render_template(
                    "home.html",
                    form=form,
                    submitted=True,
                    uploaded_file=filename,
                    chunk_count=len(chunks),
                    collection_name=collection_name,
                    vector_store_ready=vector_store is not None,
                )
            except Exception as exc:
                error = str(exc)

    return render_template(
        "home.html",
        form=form,
        submitted=False,
        error=error,
    )