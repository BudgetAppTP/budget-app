from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class IncomeForm(FlaskForm):
    date = DateField(
        "Dátum",
        validators=[DataRequired(message="Zadajte dátum vo formáte YYYY-MM-DD")],
        format="%Y-%m-%d"
    )

    description = StringField(
        "Popis",
        validators=[
            DataRequired(message="Zadajte popis"),
            Length(max=150, message="Popis môže mať maximálne 150 znakov")
        ]
    )

    amount = DecimalField(
        "Suma (€)",
        validators=[
            DataRequired(message="Zadajte sumu"),
            NumberRange(min=0, message="Suma musí byť kladné číslo")
        ],
        places=2
    )

    submit = SubmitField("Pridať záznam")

class ExpenseForm(FlaskForm):
    date = DateField(
        "Dátum",
        validators=[DataRequired(message="Zadajte dátum")],
        format="%Y-%m-%d"
    )

    category = StringField(
        "Kategória",
        validators=[DataRequired(message="Zadajte kategóriu")],
    )

    amount = DecimalField(
        "Suma (€)",
        validators=[
            DataRequired(message="Zadajte sumu"),
            NumberRange(min=0.01, message="Suma musí byť väčšia ako 0"),
        ],
        places=2,
    )

    submit = SubmitField("Pridať výdavok")
