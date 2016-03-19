from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Regexp


class LoginForm(Form):
    username = StringField('username', render_kw={"placeholder": "Username"},
                           validators=[InputRequired(), Regexp(r'^\S+$')])
    password = PasswordField('password', render_kw={"placeholder": "Password"}, validators=[InputRequired()])

    def validate(self):
        # if Form.validate(self):
        #     user = User.query.filter_by(username=self.username.data).first()
        #
        #     if user:
        #         return user.check_password(self.password.data)
        # return False
        return Form.validate(self)


class RegisterForm(Form):
    username = StringField('username', render_kw={"placeholder": "Username"},
                           validators=[InputRequired(), Regexp(r'^\S+$')])
    password = PasswordField('password', render_kw={"placeholder": "Password"}, validators=[InputRequired()])

    def validate(self):
        # if Form.validate(self):
        #     q = User.query.filter_by(username=self.username.data).count()
        #     return q == 0
        # return False
        return Form.validate(self)


class MailForm(Form):
    recipient = StringField('recipient', render_kw={"placeholder": "To"})
    subject = StringField('subject', render_kw={"placeholder": "Subject"})
    text = TextAreaField('text', render_kw={"placeholder": "Your message"})

    def validate(self):
        # q = User.query.filter_by(username=self.recipient.data).count()
        # return q == 1
        return True
