
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FloatField, SubmitField, DateField, IntegerField, HiddenField,SelectField,TimeField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    phone_number = StringField(
        'Phone Number',
        validators=[DataRequired(), Length(min=10, max=15, message="Invalid phone number length.")]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long.")]
    )
    submit = SubmitField('Login')

class AddUserForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[DataRequired(), Length(max=100, message="Name cannot exceed 100 characters.")]
    )
    phone = StringField(
        'Phone Number',
        validators=[DataRequired(), Length(min=10, max=15, message="Invalid phone number length.")]
    )
    role = SelectField('Role',
                       choices=['Admin','Assistant Head Teacher', 'Assistant Teacher'],
                       validators=[DataRequired()])
    submit = SubmitField('Add User')

    def validate_phone_number(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError("Phone number already registered.")



class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class NewsForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Title is required."),
            Length(max=255, message="Title cannot exceed 255 characters.")
        ]
    )
    content = TextAreaField(
        'Content',
        validators=[
            DataRequired(message="Content is required.")
        ]
    )
    submit = SubmitField('Post News')

class TeacherScheduleForm(FlaskForm):
    teacher = SelectField(
        'Teacher',
        coerce=int,
        validators=[DataRequired(message="Please select a teacher.")]
    )
    class_ = SelectField(
        'Class',
        coerce=int,
        validators=[DataRequired(message="Please select a class.")]
    )
    subject = SelectField(
        'Subject',
        coerce=int,
        validators=[DataRequired(message="Please select a subject.")]
    )
    day_of_week = SelectField(
        'Day of the Week',
        choices=[
            ('Sunday', 'Sunday'),
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
        ],
        validators=[DataRequired(message="Please select a day.")]
    )
    start_time = TimeField(
        'Start Time',
        validators=[DataRequired(message="Start time is required.")],
        format='%H:%M'
    )
    end_time = TimeField(
        'End Time',
        validators=[DataRequired(message="End time is required.")],
        format='%H:%M'
    )
    submit = SubmitField('Create Schedule')

