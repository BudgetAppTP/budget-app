from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

CATEGORIES_EXPENSE = [
    ("Jedlo", "Jedlo"),
    ("Byvanie", "Byvanie"),
    ("Doprava", "Doprava"),
    ("Obliekanie", "Obliekanie"),
    ("Lieky", "Lieky"),
    ("Cistiace prostriedky", "Cistiace prostriedky"),
    ("Mobil", "Mobil"),
    ("Streaming", "Streaming"),
    ("Volny cas", "Volny cas"),
    ("Investovanie", "Investovanie"),
    ("Sporenie", "Sporenie"),
]

CATEGORIES_INCOME = [
    ("Prijmy", "Prijmy"),
]

class TransactionFilterForm(FlaskForm):
    month = StringField("Mesiac (YYYY-MM)", validators=[Optional(), Length(max=7)])
    kind = SelectField("Typ", choices=[("", "Vsetko"), ("income", "Prijem"), ("expense", "Vydavok")], validators=[Optional()])
    category = SelectField("Kategoria", choices=[("", "Vsetko")] + [(c, c) for c, _ in CATEGORIES_EXPENSE + CATEGORIES_INCOME], validators=[Optional()])
    search = StringField("Hladat", validators=[Optional(), Length(max=100)])
    submit = SubmitField("Filtrovat")

class IncomeForm(FlaskForm):
    date = DateField("Datum", validators=[DataRequired(message="Zadajte datum vo formate YYYY-MM-DD")], format="%Y-%m-%d")
    category = SelectField("Kategoria", choices=CATEGORIES_INCOME, validators=[DataRequired()])
    subcategory = StringField("Podkategoria", validators=[Optional(), Length(max=100)])
    item = StringField("Polozka", validators=[Optional(), Length(max=200)])
    qty = DecimalField("Mnozstvo", validators=[DataRequired(), NumberRange(min=0)], places=2, default=1)
    unit_price = DecimalField("Jednotkova cena", validators=[DataRequired(), NumberRange(min=0)], places=2)
    vat = DecimalField("DPH", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    seller = StringField("Predajca", validators=[Optional(), Length(max=100)])
    unit = StringField("Jednotka", validators=[Optional(), Length(max=20)])
    note = TextAreaField("Poznamka", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Pridat prijem")

class ExpenseForm(FlaskForm):
    date = DateField("Datum", validators=[DataRequired(message="Zadajte datum vo formate YYYY-MM-DD")], format="%Y-%m-%d")
    category = SelectField("Kategoria", choices=CATEGORIES_EXPENSE, validators=[DataRequired()])
    subcategory = StringField("Podkategoria", validators=[Optional(), Length(max=100)])
    item = StringField("Polozka", validators=[Optional(), Length(max=200)])
    qty = DecimalField("Mnozstvo", validators=[DataRequired(), NumberRange(min=0)], places=2, default=1)
    unit_price = DecimalField("Jednotkova cena", validators=[DataRequired(), NumberRange(min=0)], places=2)
    vat = DecimalField("DPH", validators=[Optional(), NumberRange(min=0)], places=2, default=0.2)
    seller = StringField("Predajca", validators=[Optional(), Length(max=100)])
    unit = StringField("Jednotka", validators=[Optional(), Length(max=20)])
    note = TextAreaField("Poznamka", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Pridat vydavok")
