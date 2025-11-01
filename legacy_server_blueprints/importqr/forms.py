from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField, SubmitField, HiddenField
from wtforms.validators import Optional, Length

class ImportQrForm(FlaskForm):
    payload = TextAreaField("JSON vstup", validators=[Optional(), Length(max=200000)])
    file = FileField("Subor s JSON")
    action = HiddenField()
    submit_preview = SubmitField("Nahlad")
    submit_confirm = SubmitField("Potvrdit a importovat")
