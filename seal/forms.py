from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo
from flask_login import current_user
from seal.models import User, Sample
from seal import bcrypt


################################################################################
# Authentication


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=20)]
    )
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    mail = StringField(
        'Mail',
        validators=[Optional(), Email()]
    )
    image_file = FileField(
        'Update Profile Picture',
        validators=[FileAllowed(['png', 'jpg', 'jpeg'])]
    )
    submit_update = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose another one.')

    def validate_mail(self, mail):
        if mail.data != current_user.mail:
            user = User.query.filter_by(mail=mail.data).first()
            if user:
                raise ValidationError('That mail is already taken. Please choose another one.')


class UpdatePasswordForm(FlaskForm):
    old_password = PasswordField(
        'Old Password',
        validators=[DataRequired(), Length(min=6, max=20)]
    )
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=6, max=20)]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('new_password')]
    )
    submit_password = SubmitField('Update Password')

    def validate_old_password(self, old_password):
        if not bcrypt.check_password_hash(current_user.password, self.old_password.data):
            raise ValidationError('That password is incorrect!')


################################################################################


class UploadVariantForm(FlaskForm):
    samplename = StringField(
        'Sample Name',
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    family = StringField(
        'Family ID',
        validators=[Optional(), Length(min=2, max=20)]
    )
    vcf_file = FileField(
        'Upload VCF file',
        validators=[DataRequired(), FileAllowed(['vcf', 'vcf.gz'])]
    )
    carrier = BooleanField('Carrier')
    index = BooleanField('Index')

    submit = SubmitField('Create New Sample')

    def validate_samplename(self, samplename):
        sample = Sample.query.filter_by(samplename=samplename.data).first()
        if sample:
            raise ValidationError('This Sample Name is already in database!')


class AddCommentForm(FlaskForm):
    comment = TextAreaField(
        'Comment',
        validators=[DataRequired(), Length(min=2)]
    )

    submit = SubmitField('Add A Comment')


################################################################################
