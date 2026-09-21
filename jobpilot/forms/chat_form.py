from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Optional, URL


class ChatForm(FlaskForm):
    file = FileField(
        "Upload file",
        validators=[
            FileAllowed(
                ["pdf", "doc", "docx", "txt", "md", "csv"],
                "Only PDF, Word, text, and CSV files are allowed.",
            )
        ],
    )
    job_description = TextAreaField(
        "Job description",
        validators=[Optional()],
    )
    job_link = StringField(
        "Job link",
        validators=[Optional(), URL(message="Please enter a valid URL.")],
    )
    submit = SubmitField("Submit")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        file_present = bool(self.file.data)
        jd_present = bool(self.job_description.data and self.job_description.data.strip())
        link_present = bool(self.job_link.data and self.job_link.data.strip())

        if not (file_present or jd_present or link_present):
            self.job_description.errors.append(
                "Please upload a file, paste a job description, or provide a link."
            )
            return False

        if jd_present and link_present:
            self.job_link.errors.append(
                "Provide either a job description or a job link, not both."
            )
            return False

        return True

