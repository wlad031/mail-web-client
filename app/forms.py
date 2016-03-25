from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Regexp


class LoginForm(Form):
    username = StringField('username', render_kw={"placeholder": "Email"},
                           validators=[InputRequired(), Regexp(r'^\S+$')])
    password = PasswordField('password', render_kw={"placeholder": "Password"}, validators=[InputRequired()])

    def validate(self):
        return Form.validate(self)


class RegisterForm(Form):
    username = StringField('username', render_kw={"placeholder": "Login"},
                           validators=[InputRequired(), Regexp(r'^\S+$')])
    password = PasswordField('password', render_kw={"placeholder": "Password"}, validators=[InputRequired()])

    def validate(self):
        return Form.validate(self)


class MailForm(Form):
    recipient = StringField('recipient', render_kw={"placeholder": "To"})
    subject = StringField('subject', render_kw={"placeholder": "Subject"})
    text = TextAreaField('text', render_kw={"placeholder": "Your message"})

    def validate(self):
        return True
