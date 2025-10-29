from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class MonthSelectForm(FlaskForm):
    month = StringField("Mesiac (YYYY-MM)", validators=[Optional(), Length(max=7)])
    submit = SubmitField("Zobrazit")

class BudgetItemForm(FlaskForm):
    id = HiddenField()
    month = HiddenField()
    section = HiddenField()
    limit_amount = DecimalField("Limit", validators=[DataRequired(), NumberRange(min=0)], places=2)
    percent_target = DecimalField("Percento ciela", validators=[Optional(), NumberRange(min=0, max=100)], places=2)
    submit = SubmitField("Ulozit")

class BudgetListForm(FlaskForm):
    month = HiddenField()
    submit = SubmitField("Ulozit zmeny")
