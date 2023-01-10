from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo
from flask_login import current_user
from seal.models import User, Sample, Run, Team, Bed, Region
from seal import bcrypt
import pandas as pd
import requests

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
    api_key_md = StringField(
        'API_key_md',
        validators=[Optional()]
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

    def validate_api_key_md(self, api_key_md):
        payload = {'api_key': api_key_md.data}
        r = requests.post("https://mobidetails.iurc.montp.inserm.fr/MD/api/service/check_api_key", data=payload)
        response = r.json()
        if not response["api_key_pass_check"]:
            raise ValidationError(f'API key status {response["api_key_status"]}. Please check your API key.')


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
        validators=[DataRequired(), EqualTo('new_password', "Passwords must match!")]
    )
    submit_password = SubmitField('Update Password')

    def validate_old_password(self, old_password):
        if not bcrypt.check_password_hash(current_user.password, self.old_password.data):
            raise ValidationError('That password is incorrect!')

    def validate_new_password(self, new_password):
        if bcrypt.check_password_hash(current_user.password, self.new_password.data):
            raise ValidationError('Your new password must be different from your previous password!')


################################################################################


class UploadVariantForm(FlaskForm):
    samplename = StringField(
        'Sample Name',
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    family = StringField(
        'Family',
        validators=[Optional(), Length(min=2, max=20)]
    )
    run = StringField(
        'Run',
        validators=[Optional(), Length(min=2, max=50)]
    )
    vcf_file = FileField(
        'Upload VCF file',
        validators=[DataRequired(), FileAllowed(['vcf', 'vcf.gz'])]
    )
    affected = BooleanField('Affected')
    index = BooleanField('Index')

    teams = SelectMultipleField('Teams', coerce=int)

    submit = SubmitField('Create New Sample')

    def validate_samplename(self, samplename):
        run = Run.query.filter_by(name=self.run.data).first()
        if run:
            sample = Sample.query.filter_by(samplename=samplename.data, runid=run.id).first()
        else:
            sample = Sample.query.filter_by(samplename=samplename.data, runid=None).first()
        if sample:
            raise ValidationError('This Sample Name is already in database!')


class UploadPanelForm(FlaskForm):
    name = StringField(
        'Panel Name',
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    bed = FileField(
        'Upload file',
        validators=[DataRequired(), FileAllowed(['bed', 'txt', 'csv', 'tsv'])]
    )
    teams_choices = [(team.id, team.teamname) for team in Team.query.all()]
    teams = SelectMultipleField('Teams', choices=teams_choices, coerce=int)

    submit = SubmitField('Create New Panel')

    def validate_name(self, name):
        bed_name = Bed.query.filter_by(name=name.data).first()
        if bed_name:
            raise ValidationError('This Panel Name is already in database! Please choose another one.')

    def validate_bed(self, bed):
        self.df = pd.read_csv(bed.data, sep='\t', header=None)
        if len(self.df.columns) == 2 or len(self.df.columns) > 12:
            raise ValidationError('Error when parsing file : BED or list of Region name.')
        for index, row in self.df.iterrows():
            if len(self.df.columns) == 1:
                region = Region.query.filter_by(name=row[0]).first()
                if not region:
                    raise ValidationError(f'Region: "{row[0]}" not found in SEAL.')


class AddCommentForm(FlaskForm):
    comment = TextAreaField(
        'Comment',
        validators=[DataRequired(), Length(min=2)]
    )

    submit = SubmitField('Add A Comment')


class SaveFilterForm(FlaskForm):
    filterName = StringField(
        'Filter Name',
        validators=[DataRequired(), Length(min=2, max=20)]
    )

    teams = SelectMultipleField('Teams', coerce=int)

    filterText = TextAreaField(
        'Filters',
        validators=[DataRequired()]
    )

    submit = SubmitField('Add A New Filter')


################################################################################
