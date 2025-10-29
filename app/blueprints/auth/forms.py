from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Heslo", validators=[DataRequired(), Length(min=6, max=255)])
    submit = SubmitField("Prihlasit sa")

class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Heslo", validators=[DataRequired(), Length(min=6, max=255)])
    confirm = PasswordField("Potvrdit heslo", validators=[DataRequired(), EqualTo("password", message="Hesla sa nezhoduju")])
    submit = SubmitField("Vytvorit ucet")
