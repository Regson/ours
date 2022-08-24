from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms import validators
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, EqualTo
from wtforms.widgets import TextArea
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField

# create a Userform class
class UsersForm(FlaskForm):
    name = StringField("Name", validators = [DataRequired()])
    username = StringField("username", validators = [DataRequired()])
    email = StringField("Email", validators = [DataRequired()])
    favorite_color = StringField("Favorite Color")
    about_author = TextAreaField("About Author")
    profile_pic = FileField("Profile pic")
    pw_hash = PasswordField("Password", validators = [DataRequired(), EqualTo('confirm_pw', message="Repeat password")])
    confirm_pw = PasswordField("Confirm Password", validators = [DataRequired()])
    submit = SubmitField("Submit")

# create a form class
class NameForm(FlaskForm):
    name = StringField("What's Your Name", validators = [DataRequired()])
    submit = SubmitField("Submit")


class Test_pwForm(FlaskForm):
    email = StringField("What's Your Email", validators = [DataRequired()])
    pw = PasswordField("What's Your Password", validators = [DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField("Username", validators = [DataRequired()])
    password = PasswordField("Password", validators = [DataRequired()])
    submit = SubmitField("Login")

class PostsForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    topics = StringField("Topics", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    content = CKEditorField("Content", validators=[DataRequired()])
    post_image = FileField("Image")
    submit = SubmitField("submit")
    

class SearchForm(FlaskForm):
    searched = StringField("searched", validators = [DataRequired()])
    submit = SubmitField("search")
