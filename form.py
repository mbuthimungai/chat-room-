from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo


## The class creates a flask form 
## which is a wtform 
class RegisterForm(FlaskForm):
    f_name = StringField(label="First Name", validators=[DataRequired(), Length(max=28)], render_kw={"placeholder":"Enter first name"})
    l_name = StringField(label="Last Name", validators=[DataRequired(), Length(max=28)], render_kw={"placeholder":"Enter last name"})
    email = EmailField(label="Email", validators=[DataRequired(), Length(max=28), Email(message="Not a Valid email address")], render_kw={"placeholder":"Enter email"})
    password = StringField(label="password", validators=[DataRequired(), Length(min=6, max=28), EqualTo(fieldname="confirm_password", message="password does not match")], render_kw={"placeholder": "Enter Password"})
    confirm_password = StringField(label="confirm password", validators=[DataRequired(), Length(min=6, max=28)], render_kw={"placeholder": "confirm your password"})
    submit = SubmitField(label="Register")

class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Length(max=28), Email(message="Not a Valid email address")], render_kw={"placeholder":"Enter email"})
    password = StringField(label="password", validators=[DataRequired(), Length(min=6, max=28)], render_kw={"placeholder": "Enter Password"})
    submit = SubmitField(label="Login")

class AddGroupForm(FlaskForm):
    title = StringField(label="Title", validators=[DataRequired(), Length(max=28), ], render_kw={"placeholder":"Enter group title"})    
    submit = SubmitField(label="register group")

class PostForm(FlaskForm):
    text = TextAreaField(validators=[DataRequired(), ], render_kw={"placeholder": "create a post here"})
    submit = SubmitField(label="post")