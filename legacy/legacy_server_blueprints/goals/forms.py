from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

SECTIONS = [
    ("", "Ziadna"),
    ("POTREBY", "POTREBY"),
    ("VOLNY_CAS", "VOLNY_CAS"),
    ("SPORENIE", "SPORENIE"),
    ("INVESTOVANIE", "INVESTOVANIE"),
]

class GoalsFilterForm(FlaskForm):
    section = SelectField("Sekcia", choices=SECTIONS, validators=[Optional()])
    submit = SubmitField("Filtrovat")

class GoalForm(FlaskForm):
    name = StringField("Nazov", validators=[DataRequired(), Length(max=120)])
    type = SelectField("Typ", choices=[("monthly", "mesacny"), ("longterm", "dlhodoby")], validators=[DataRequired()])
    target_amount = DecimalField("Cielova suma", validators=[DataRequired(), NumberRange(min=0)], places=2)
    section = SelectField("Sekcia", choices=SECTIONS, validators=[Optional()])
    month_from = StringField("Od mesiaca (YYYY-MM)", validators=[Optional(), Length(max=7)])
    month_to = StringField("Do mesiaca (YYYY-MM)", validators=[Optional(), Length(max=7)])
    is_done = BooleanField("Splnene")
    submit = SubmitField("Ulozit")
