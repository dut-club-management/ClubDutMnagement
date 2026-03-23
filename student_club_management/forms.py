from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms import SelectField, TextAreaField, IntegerField, DateTimeField, BooleanField, FileField, MultipleFileField

class LoginForm(FlaskForm):
    email = StringField('Email or Student Number', validators=[DataRequired(), Length(min=4, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    student_number = StringField('Student Number', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Club Forms
class ClubForm(FlaskForm):
    club_name = StringField('Club Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('', 'Select a category'),
        ('Academic', 'Academic'),
        ('Sports', 'Sports'),
        ('Cultural', 'Cultural'),
        ('Social', 'Social'),
        ('Technical', 'Technical'),
        ('Arts', 'Arts'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    max_members = IntegerField('Max Members', validators=[Optional()])
    meeting_schedule = StringField('Meeting Schedule', validators=[Optional()])
    submit = SubmitField('Create Club')

class ClubEditForm(ClubForm):
    submit = SubmitField('Update Club')

# Announcement Forms
class AnnouncementForm(FlaskForm):
    send_to = SelectField('Send To', choices=[('club_members', 'Club Members'), ('students_only', 'Students Only'), ('all_users', 'All Users')], validators=[DataRequired()])
    club_id = SelectField('Club', validators=[DataRequired(), Optional()], coerce=int)
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[('normal', 'Normal'), ('important', 'Important'), ('urgent', 'Urgent')], default='normal')
    pinned = BooleanField('Pin Announcement')
    resource_links = TextAreaField('Resource Links (one per line)')
    attachment = FileField('Attachment')
    submit = SubmitField('Publish')

# Event Forms
class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    event_date = DateTimeField('Event Date/Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeField('End Date/Time (optional)', format='%Y-%m-%dT%H:%M')
    location = StringField('Location', validators=[DataRequired()])
    max_attendees = IntegerField('Max Attendees')
    requires_club = BooleanField('Requires Club Team')
    min_club_members = IntegerField('Min Club Members')
    max_club_members = IntegerField('Max Club Members')
    club_id = SelectField('Club (optional)', coerce=int)
    submit = SubmitField('Create Event')

# Chat Forms
class ChatStartForm(FlaskForm):
    recipient_id = IntegerField('Recipient ID', validators=[DataRequired()])
    subject = StringField('Subject', validators=[Optional()])
    message = TextAreaField('Initial Message')
    submit = SubmitField('Start Conversation')

class ChatRequestForm(FlaskForm):
    message = TextAreaField('Message')
    submit = SubmitField('Send Request')
