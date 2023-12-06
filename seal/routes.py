# (c) 2023, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
#
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2023  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import functools
import json
import secrets
import urllib

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from threading import Thread

from PIL import Image
from flask import (flash, jsonify, redirect, render_template, request, url_for,
                   escape, abort)
from flask_login import current_user, login_user, logout_user
from flask_login.utils import EXEMPT_METHODS
from flask_wtf.csrf import CSRFError
from sqlalchemy import and_, or_, cast, String
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from seal import app, bcrypt, db
from seal.forms import (AddCommentForm, LoginForm, SaveFilterForm,
                        UploadPanelForm, UploadVariantForm,
                        UpdateAccountForm, UpdatePasswordForm, UploadClinvar)
from seal.models import (Bed, Comment_sample, Comment_variant, Family, Filter,
                         History, Omim, Region, Run, Sample, Team,
                         Transcript, User, Variant, Var2Sample, Patient,
                         Clinvar)
from seal.schedulers import update_clinvar_thread


###############################################################################
# Decorators/Exceptions and handler


# Here define safe host authorized for a redirection
SAFE_HOST = []


def redirect_dest(fallback='/home'):
    """
    Redirects the user to a given URL after validating it's safe.

    Args:
        fallback (str): the URL to redirect the user to if the 'next' URL is
                        invalid or unsafe.

    Returns:
        A Flask response object that redirects the user to the next URL or
        fallback URL.
    """
    dest = request.args.get('next')
    if not dest:
        return redirect(fallback)
    url = urlparse(dest)
    if url.path and (not url.netloc or url.netloc == request.host):
        return redirect(url.path)
    if url.hostname and url.hostname in SAFE_HOST:
        return redirect(url.geturl())
    else:
        flash(f"Redirection to '{url.path}' forbidden !", "error")
        return redirect(fallback)


def login_required(func):
    """
    A decorator that ensures that the user is logged in before accessing the
    decorated view. If the user is not logged in, they will be redirected to
    the login page.

    Usage:
    ------
    @login_required
    def my_view():
        # Do something here

    """
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        """
        A decorator function for enforcing user login.

        If the user is not logged in, they will be redirected to the login
        page.
        If the `LOGIN_DISABLED` configuration setting is True, then login is
        not required.
        If the user has not completed the first connection process, they will
        be redirected to the first connection page.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The decorated view function.
        """
        if request.method in EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return app.login_manager.unauthorized()
        elif request.url_rule.endpoint == "first_connexion":
            pass
        elif not current_user.logged:
            return redirect(url_for('first_connexion', next=request.url))
        return func(*args, **kwargs)
    return decorated_view


def admin_required(func):
    """
    A decorator that ensures that the user is admin before accessing the
    decorated view. If the user is not admin, they will beredirected to the
    index page.

    Usage:
    ------
    @admin_required
    def my_view():
        # Do something here

    """
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        """
        A decorator function for enforcing user login.

        If the user is not admin, they will be redirected to the index page.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The decorated view function.
        """
        if request.method in EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif not current_user.admin:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


# https://flask.palletsprojects.com/en/2.2.x/errorhandling/
class InvalidAPIUsage(Exception):
    """
    Exception class for handling invalid API usage errors.

    Attributes:
        message (str): The error message.
        status_code (int): The HTTP status code to return (default 400).
        payload (dict): Additional data to include in the response (optional).
    """

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """
        Returns a dictionary with the error message and any additional payload
        data.

        Returns:
            dict: A dictionary with the error message and payload data.
        """

        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(e):
    """
    Error handler function for handling invalid API usage errors.

    Args:
        e (InvalidAPIUsage): The exception object.

    Returns:
        str: A JSON response containing the error message and status code.
    """

    return jsonify(e.to_dict()), e.status_code


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
    Handles a CSRF error.

    Args:
        e: A Flask-WTF CSRF error.

    Returns:
        A redirect to the index page with a flash message.
    """
    flash(f"{e.name} : {e.description} Please Retry.", 'warning')

    return redirect_dest()


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(406)
@app.errorhandler(408)
@app.errorhandler(410)
@app.errorhandler(500)
def handle_http_error(e):
    """Error handler to render the error template.

    Args:
        e (Exception): The error exception.

    Returns:
        The rendered template with the error information.
    """
    return render_template(
        "essentials/error.html",
        title=e.code,
        e=e
    )


###############################################################################


###############################################################################
# Utilities


# https://www.tutorialspoint.com/python-check-if-two-lists-have-any-element-in-common
def has_common_elements(list_1, list_2):
    """
    Check if two lists have any element in common.

    Args:
        list_1 (list): First list to check.
        list_2 (list): Second list to check.

    Returns:
        bool: True if there is any common element or one list is empty,
              False otherwise.
    """

    if not list_1 or not list_2:
        return True
    for value in list_1:
        if value in list_2:
            return True
    return False


def crop_center(pil_img, crop_width, crop_height):
    """
    Crop the center of the image to the specified width and height.

    Args:
        pil_img (PIL.Image): A PIL image to crop.
        crop_width (int): The desired width to crop the image to.
        crop_height (int): The desired height to crop the image to.

    Returns:
        PIL.Image: The cropped PIL image.
    """

    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    """
    Crop the image to the maximum square.

    Args:
        pil_img (PIL.Image): A PIL image to crop.

    Returns:
        PIL.Image: The cropped PIL image.
    """

    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))



def save_picture(form_picture):
    """Saves a user's profile picture to the file system.

    Args:
        form_picture (FileStorage): The user's profile picture.

    Returns:
        str: The filename of the saved profile picture.
    """
    random_hex = secrets.token_hex(8)
    f_ext = Path(form_picture.filename).suffix
    picture_fn = random_hex + f_ext
    picture_path = Path(app.root_path).joinpath('static', 'images', 'profile',
                                                picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i = crop_max_square(i).resize(output_size, Image.LANCZOS)
    i.save(picture_path)

    return picture_fn


def add_vcf(info, vcf_file):
    """
    Save uploaded VCF file and corresponding sample information to disk.

    Parameters:
    info (dict): Sample information, including samplename, affected, index,
                 userid, date, family, run, filter, bed, teams.
    vcf_file (FileStorage): Uploaded VCF file.

    Returns:
        str: Filename of saved VCF file.
    """
    random_hex = secrets.token_hex(8)

    f_ext = Path(vcf_file.filename).suffix

    vcf_fn = random_hex + f_ext
    vcf_path_base = Path(app.root_path).joinpath('static/temp/vcf/')
    vcf_path = vcf_path_base.joinpath(vcf_fn)
    vcf_file.save(vcf_path)

    info["vcf_path"] = str(vcf_path)

    token_fn = random_hex + ".token"
    token_path = vcf_path_base.joinpath(token_fn)
    with open(token_path, "w") as tf:
        tf.write(json.dumps(info))

    return vcf_fn


###############################################################################


###############################################################################
# Basics views


@app.route("/")
@app.route("/home")
@login_required
def index():
    """
    Renders the home page of the application.

    Returns:
        A rendered template for the home page.
    """
    return render_template(
        "essentials/home.html",
        title="Home"
    )


@app.route("/about")
def about():
    """
    Renders the about page of the application.

    Returns:
        A rendered template for the about page.
    """
    return render_template(
        "essentials/about.html",
        title="About"
    )


@app.route("/contact")
def contact():
    """
    Renders the contact page of the application.

    Returns:
        A rendered template for the contact page.
    """
    return render_template(
        "essentials/contact.html",
        title="Contact"
    )


@app.route("/maintenance")
def maintenance():
    """
    Check if the website is under maintenance, and redirect to the homepage if
    not.

    Returns:
        A rendered template for the maintenace page or redirect to index.
    """
    if not app.config["MAINTENANCE"]:
        return redirect(url_for("index"))
    return render_template(
        "essentials/maintenance.html",
        reason=app.config["MAINTENANCE_REASON"]
    )


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    """
    View function that logs out the current user and redirects to the login
    page.

    Returns:
        flask.redirect: A redirect response to the login page.
    """
    logout_user()
    flash("You have been disconnected!", "warning")
    return redirect(url_for('login'))

###############################################################################


###############################################################################
# Authentication


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Handle user authentication.

    If the user is already authenticated, redirect to the home page.
    If the user submits a valid login form, log them in and redirect them to
    the next page (if specified).
    If the form is not valid, render the login page with appropriate error
    messages.

    Returns:
        A rendered template for the login page or redirect.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')

            if not user.logged:
                return redirect(url_for('first_connexion', next=next_page))

            flash(f'You are logged in as: {user.username}!', 'success')
            return redirect_dest()
        else:
            flash('Login unsuccessful. Please check username and/or password!',
                  'error')

    return render_template(
        "authentication/login.html",
        title="Login",
        form=form
    )


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """
    Displays and edits the user's account information. The user can edit their
    username, email, and profile picture. If the user submits the
    'update_account_form', the function will validate it and update the user's
    information in the database. If the user submits the
    'update_password_form', the function will validate it, generate a new
    password hash and store it in the database.

    Returns:
        Rendered HTML template for 'authentication/account.html'.
    """
    update_account_form = UpdateAccountForm()
    update_password_form = UpdatePasswordForm()
    if ("submit_update" in request.form
            and update_account_form.validate_on_submit()):
        if update_account_form.image_file.data:
            picture_file = save_picture(update_account_form.image_file.data)
            current_user.image_file = picture_file

        if update_account_form.mail.data != '':
            current_user.mail = update_account_form.mail.data
        else:
            current_user.mail = None

        if update_account_form.api_key_md.data != '':
            current_user.api_key_md = update_account_form.api_key_md.data
        else:
            current_user.api_key_md = None

        current_user.username = update_account_form.username.data
        db.session.commit()

        flash('Your account has been updated!', 'success')
    elif ("submit_password" in request.form
            and update_password_form.validate_on_submit()):
        pwd = update_password_form.new_password.data
        current_user.password = bcrypt.generate_password_hash(pwd).decode('utf-8')
        db.session.commit()
        flash('Your password has been changed!', 'success')

    update_account_form.username.data = current_user.username
    update_account_form.mail.data = current_user.mail
    update_account_form.api_key_md.data = current_user.api_key_md

    return render_template(
        'authentication/account.html', title='Account',
        update_account_form=update_account_form,
        update_password_form=update_password_form)


@app.route("/first_connexion", methods=['GET', 'POST'])
@login_required
def first_connexion():
    """
    Prompts the user to change their password during their first login. If the
    user submits the 'update_password_form', the function will validate it,
    generate a new password hash, store it in the database, and set the
    'logged' flag to 'True'. Once the 'logged' flag is set, the user will be
    redirected to the 'next_page' or 'index'.

    Returns:
        Rendered HTML template for 'authentication/first_connexion.html'.
    """
    update_password_form = UpdatePasswordForm()
    next_page = request.args.get('next')
    if current_user.logged:
        return redirect_dest()
    if ("submit_password" in request.form
            and update_password_form.validate_on_submit()):
        pwd = update_password_form.new_password.data
        current_user.password = bcrypt.generate_password_hash(pwd).decode('utf-8')
        current_user.logged = True
        db.session.commit()
        flash('Your password has been changed!', 'success')
        return redirect_dest()

    return render_template(
        'authentication/first_connexion.html', title='First Connexion',
        update_password_form=update_password_form)


###############################################################################


###############################################################################
# Analysis


@app.route("/transcripts", methods=['GET', 'POST'])
@login_required
def transcripts():
    """
    Displays the transcripts page, which allows the user to view transcripts.

    Returns:
        A Flask template for the transcripts page.
    """
    return render_template('analysis/transcripts.html', title='Transcripts')


@app.route("/sample/<int:id>", methods=['GET', 'POST'])
@login_required
def sample(id):
    """
    Displays the sample page for a specific sample.

    Args:
        id: The id of the sample to display.

    Returns:
        A Flask template for the sample page for the specified sample or
        redirect to index.
    """
    sample = Sample.query.get(id)
    if not sample:
        flash(f"Sample '{id}' not found! Please contact admin!",
              category="error")
        return redirect(url_for('index'))

    commentForm = AddCommentForm()
    saveFilterForm = SaveFilterForm()

    choices = [(team.id, team.teamname) for team in Team.query.all()]
    saveFilterForm.teams.choices = choices
    saveFilterForm.teams.data = [team.id for team in current_user.teams]

    count_hide=0

    for v in  Var2Sample.query.filter(Var2Sample.sample_ID == id, Var2Sample.hide == True):
        if v.inBed():
            count_hide+=1

    samples = {
        "family": [],
        "same": []
    }
    if sample.patient and sample.patient.family:
        for p in sample.patient.family.patients:
            t = "same" if p == sample.patient else "family"
            for s in p.samples:
                if s != sample and s.status > 0:
                    samples[t].append(s)

    clinvar = Clinvar.query.filter(Clinvar.genome == "grch37", Clinvar.current == True).one()

    return render_template(
        'analysis/sample.html', title=f'{sample.samplename}',
        sample=sample,
        count_hide = count_hide,
        family_members = samples["family"],
        other_samples = samples["same"],
        form=commentForm,
        saveFilterForm=saveFilterForm,
        clinvar = clinvar
    )


@app.route('/create/sample', methods=['GET', 'POST'])
@login_required
def create_variant():
    form = UploadVariantForm()

    # Add choices for bed
    form.bed.choices=[('0', 'Choose a bed')] + [(b.id, b.name) for b in Bed.query.filter(Bed.teams == None).all()]
    for t in current_user.teams:
        for b in t.beds:
            form.bed.choices.append((b.id, b.name))

    # Add choices for filter
    form.filter.choices=[(f.id, f.filtername) for f in Filter.query.filter(Filter.teams == None).order_by(Filter.id.asc()).all()]
    for t in current_user.teams:
        for f in t.filters:
            form.filter.choices.append((f.id, f.filtername))

    # Add choices for teams
    choices = [(team.id, team.teamname) for team in Team.query.all()]
    form.teams.choices = choices
    form.teams.data = [team.id for team in current_user.teams]
    
    if form.validate_on_submit():
        print(request.form)

        info = {
            "patient": {
                "id": form.patientID.data,
                "alias": form.patient_alias.data,
                "affected": form.affected.data,
                "index": form.index.data
            },
            "family": {
                "name": form.family.data
            },
            "samplename": form.samplename.data,
            "userid": current_user.id,
            "date": str(datetime.now()),
            "run": {
                "name": form.run.data,
                "alias": form.run_alias.data,
            },
            "filter": {
                "id": form.filter.data,
            },
            "bed": {
                "id": form.bed.data,
            },
            "teams": [
                {"name": Team.query.get(id).teamname} for id in form.teams.data
            ],
            "interface": True
        }
        print(info)
        add_vcf(info, form.vcf_file.data)

        flash(f'Sample {form.samplename.data} will be added soon!',
              'info')
        return redirect(url_for('index'))

    content = {
        'form': form,
    }
    return render_template('analysis/create_sample.html', **content)


@app.route("/create/panel", methods=['GET', 'POST'])
@login_required
def create_panel():
    """
    View function for creating a new panel.

    If the form is submitted, adds the panel and its regions to the database
    and returns to the index page.
    If the form is not submitted, displays the upload form.

    Returns:
        A rendered template of the upload panel form.
    """
    uploadPanelForm = UploadPanelForm()
    if "submit" in request.form and uploadPanelForm.validate_on_submit():
        panel = Bed(name=uploadPanelForm.name.data)
        panel.teams = [Team.query.get(team_id) for team_id in uploadPanelForm.teams.data]
        db.session.add(panel)
        for index, row in uploadPanelForm.df.iterrows():
            if len(uploadPanelForm.df.columns) == 1:
                region = Region.query.filter_by(name=row[0]).all()
                for r in region:
                    panel.regions.append(r)
            if (len(uploadPanelForm.df.columns) >= 3) and (len(uploadPanelForm.df.columns) <= 12):
                random_hex = secrets.token_hex(8)
                name = f"{random_hex}-{row[3]}" if 3 in row else random_hex
                region = Region(name=name, chr=row[0], start=row[1], stop=row[2])
                db.session.add(region)
                panel.regions.append(region)
        db.session.commit()
        flash(f'New Panel Uploaded : {uploadPanelForm.name.data}', 'success')
        return redirect(url_for('index'))

    uploadPanelForm.teams.data = [team.id for team in current_user.teams]

    return render_template(
        'analysis/panel.html', title="Add Panel",
        form=uploadPanelForm
    )


@app.route("/update/clinvar", methods=['GET', 'POST'])
@login_required
@admin_required
def update_clinvar():
    UploadClinvarForm = UploadClinvar()

    if "submit" in request.form and UploadClinvarForm.validate_on_submit():
        version = int(UploadClinvarForm.version.data.strftime("%Y%m%d"))
        genome = UploadClinvarForm.genome_version.data

        vcf_path = Path(app.root_path).joinpath(f'static/temp/clinvar/{genome}')
        vcf_path = vcf_path.joinpath(UploadClinvarForm.vcf_file.data.filename)
        UploadClinvarForm.vcf_file.data.save(vcf_path)

        Thread(target=update_clinvar_thread, args=(vcf_path, version, genome, )).start()

        return redirect(url_for('index'))

    return render_template(
        'admin/updateclinvar.html', title="Update ClinVar",
        form=UploadClinvarForm
    )


###############################################################################


###############################################################################
# JSON views

@app.route("/json/families", methods=['GET', 'POST'])
@login_required
def json_families():
    """
    Endpoint for retrieving a list of all families in the database.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a family in the
                database.
            Each dictionary has the following keys:
            - id: The unique identifier of the family.
            - family: The name of the family.
    """
    families = Family.query.all()
    families_json = {"data": list()}
    for family in families:
        families_json["data"].append({
            "id": family.id,
            "family": family.family
        })
    return jsonify(families_json)

@app.route("/json/patients", methods=['GET', 'POST'])
@login_required
def json_patients():
    """
    Endpoint for retrieving a list of all patients in the database.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a family in the
                database.
            Each dictionary has the following keys:
            - id: The unique identifier of the family.
            - family: The name of the family.
    """
    patients = Patient.query.all()
    patients_json = {"data": list()}
    for patient in patients:
        patients_json["data"].append({
            "id": patient.id,
            "alias":patient.alias,
            "affected":patient.affected,
            "index":patient.index,
            "family": patient.family.family if patient.family else None
        })
        
    return jsonify(patients_json)


@app.route("/json/runs", methods=['GET', 'POST'])
@login_required
def json_runs():
    """
    Endpoints for retrieving a the list of all runs.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a run
            Each dictionary has the following keys:
            - id: the unique identifier of the run
            - name: the name of the run
            - alias: the alias of the run
    """
    runs = Run.query.all()
    runs_json = {"data": list()}
    for run in runs:
        runs_json["data"].append({
            "id": run.id,
            "name": run.name,
            "alias": run.alias
        })
    return jsonify(runs_json)


@app.route("/json/samples", methods=['GET', 'POST'])
@login_required
def json_samples():
    """
    Endpoints for retrieving a list of all samples.


    Returns:
        A JSON object with the following keys:
        - recordsTotal: Total samples
        - recordsFiltered: Total samples filtered
        - data: A list of dictionaries, each representing a sample
            Each dictionary has the following keys:
            - id: the unique identifier of the sample
            - samplename: the name of the sample
            - family: the family the sample belongs to (if any)
            - run: a dictionary containing the name and alias of the run the
                   sample belongs to (if any)
            - status: the status of the sample
            - lastAction: the last action concerning this sample
                - date: when it append
                - user: who did it
                - action: what it does
            - teams: a list of dictionaries, each containing the name and color
                     of a team associated with the sample
    """
    key_list = {
        "asc": [
            Sample.samplename.asc(),
            Patient.id.asc(),
            Family.family.asc(),
            Run.name.asc(),
            Run.alias.asc(),
            Sample.status.asc(),
            Sample.lastAction.asc()
        ],
        "desc": [
            Sample.samplename.desc(),
            Patient.id.desc(),
            Family.family.desc(),
            Run.name.desc(),
            Run.alias.desc(),
            Sample.status.desc(),
            Sample.lastAction.desc()
        ]
    }
    filters = or_(
        Sample.samplename.op('~')(request.form['search[value]']),
        cast(Patient.id, String).op('~')(request.form['search[value]']),
        Family.family.op('~')(request.form['search[value]']),
        Run.name.op('~')(request.form['search[value]']),
        Run.alias.op('~')(request.form['search[value]'])
    )

    samples = Sample.query
    if not current_user.admin:
        filter_samples_teams = or_(
            Sample.teams.any(Team.id.in_([t.id for t in current_user.teams])),
            Sample.teams == None
        )
        samples = samples.filter(filter_samples_teams)
    recordsTotal = samples.count()
    samples_filter = samples.outerjoin(Run, Sample.run)\
                            .outerjoin(Patient, Sample.patient).outerjoin(Family, Patient.family)\
                                .filter(filters)
    recordsFiltered = samples_filter.count()
    samples = samples_filter\
        .order_by(key_list[request.form['order[0][dir]']][int(request.form['order[0][column]'])])\
        .offset(request.form["start"])\
        .limit(request.form["length"])\
        .all()
    samples_json = {
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": list()
    }

    for sample in samples:
        teams = []
        for team in sample.teams:
            teams.append({"teamname": team.teamname, "color": team.color})
        samples_json["data"].append({
            "id": sample.id,
            "samplename": sample.samplename,
            "family": sample.patient.family.family if (sample.patient and sample.patient.familyid) else None,
            "patient": {
                "id": sample.patient_id,
                "alias": sample.patient.alias if sample.patient else None,
            },
            "run": {
                "name": sample.run.name if sample.runid else None,
                "alias": sample.run.alias if sample.runid else None 
            },
            "status": sample.status,
            "lastAction": {
                "date": sample.lastAction.date.strftime("%Y/%m/%d %H:%M:%S") if sample.lastAction else None,
                "user": sample.lastAction.user.username if sample.lastAction else None,
                "action": sample.lastAction.action if sample.lastAction else None
            },
            "teams": teams
        })
    return jsonify(samples_json)



@app.route("/json/comments/sample/<int:id>", methods=['GET', 'POST'])
@login_required
def json_comments_sample(id):
    """
    Endpoint for retrieving all comments associated with a particular sample.

    Args:
        id (int): The unique identifier of the sample.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a comment associated
                with the sample.
            Each dictionary has the following keys:
            - id: The unique identifier of the comment.
            - comment: The text of the comment.
            - sample: The sample that the comment is associated with.
            - date: The date and time that the comment was posted
                    (formatted as "YYYY/MM/DD HH:MM:SS").
            - userid: The unique identifier of the user who posted the comment.
            - username: The username of the user who posted the comment.
    """
    sample = Sample.query.get(int(id))
    comments = {
        "data": list()
    }
    for comment in sample.comments:
        comments["data"].append({
            "id": comment.id,
            "comment": comment.comment,
            "sample": str(comment.sample),
            "date": comment.date.strftime("%Y/%m/%d %H:%M:%S"),
            "userid": comment.user.id,
            "username": comment.user.username
        })
    return jsonify(comments)


@app.route("/json/variants/sample/<int:id>", methods=['GET', 'POST'])
@app.route("/json/variants/sample/<int:id>/bed/<int:idbed>", methods=['GET', 'POST'])
@app.route("/json/variants/sample/<int:id>/version/<int:version>", methods=['GET', 'POST'])
@login_required
def json_variants(id, idbed=False, version=-1):
    """
    Endpoint for retrieving all variants associated with a particular sample.

    Args:
        id (int): The unique identifier of the sample.
        idbed (int, optional): The unique identifier of the bed file.
                               Default is False.
        version (int, optional): The version number of the sample.
                                 Default is -1.


    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a variant associated
                with the sample.
            Each dictionary has the following keys:
            - annotations: A dictionary containing the main annotation for the
                           variant.
            - chr: The chromosome where the variant is located.
            - id: The identifier of the variant.
            - pos: The position of the variant.
            - ref: The reference sequence for the variant.
            - alt: The alternate sequence for the variant.
            - filter: The filter status of the variant in the sample.
            - depth: The sequencing depth of the variant in the sample.
            - reported: A boolean indicating whether the variant was reported
                        in the sample.
            - class_variant: The class of the variant.
            - allelic_depth: The allelic depth of the variant in the sample.
            - allelic_frequency: The allelic frequency of the variant in the
                                 sample.
            - inseal: A dictionary containing information about the variant in
                      SEAL database.
                - occurrences: The number of occurrences of the variant.
                - total_samples: The total number of samples.
                - occurrences_family: The number of occurrences of the variant
                                      within the same family.
                - family_members: A list of family members with the variant.
            - phenotypes: A list of phenotypes associated with the variant.
    """
    sample = Sample.query.get(int(id))
    if not sample:
        flash(f"Sample '{id}' not found! Please contact admin!",
              category="error")
        return redirect(url_for('index'))

    if idbed >= 1:
        bed = Bed.query.get(int(idbed))

    variants = {"data": list()}

    # Get all canonical trancripts

    ##################################################

    for var2sample in sample.variants:
        variant = var2sample.variant
        try:
            if bed and not bed.varInBed(variant):
                continue
        except NameError:
            pass
        if var2sample.hide:
            continue
        annotations = variant.annotations
        main_annot = None
        consequence_score = -999
        canonical = False
        refseq = False
        protein_coding = False
        preferred_transcript = False

        # try:
        #     if float(annotations[version]["ANN"][0]["gnomADg_AF"]) > 0.02:
        #         continue
        # except (ValueError, TypeError) as e:
        #     pass
        for annot in annotations[version]["ANN"]:
            current_consequence_score = annot['consequenceScore']
            current_canonical = annot['canonical']
            current_refseq = True if annot['SOURCE'] == 'RefSeq' else False
            current_protein_coding = True if annot['BIOTYPE'] == 'protein_coding' else False
            current_preferred_transcript = True if annot['Feature'] in current_user.transcripts else False

            if preferred_transcript == current_preferred_transcript:
                if refseq == current_refseq:
                    if current_protein_coding and not protein_coding:
                        canonical = current_canonical
                        consequence_score = current_consequence_score
                        refseq = current_refseq
                        protein_coding = current_protein_coding
                        preferred_transcript = current_preferred_transcript
                        annot["preferred"] = preferred_transcript
                        main_annot = annot
                        continue
                    if protein_coding and not current_protein_coding:
                        continue
                    if canonical and not current_canonical:
                        continue
                    if not canonical and current_canonical:
                        canonical = current_canonical
                        consequence_score = current_consequence_score
                        refseq = current_refseq
                        protein_coding = current_protein_coding
                        preferred_transcript = current_preferred_transcript
                        annot["preferred"] = preferred_transcript
                        main_annot = annot
                        continue
                    if current_consequence_score > consequence_score:
                        canonical = current_canonical
                        consequence_score = current_consequence_score
                        refseq = current_refseq
                        protein_coding = current_protein_coding
                        preferred_transcript = current_preferred_transcript
                        annot["preferred"] = preferred_transcript
                        main_annot = annot
                        continue
                    continue

                if current_refseq:
                    canonical = current_canonical
                    consequence_score = current_consequence_score
                    refseq = current_refseq
                    protein_coding = current_protein_coding
                    preferred_transcript = current_preferred_transcript
                    annot["preferred"] = preferred_transcript
                    main_annot = annot
                    continue
                continue

            if current_preferred_transcript:
                canonical = current_canonical
                consequence_score = current_consequence_score
                refseq = current_refseq
                protein_coding = current_protein_coding
                preferred_transcript = current_preferred_transcript
                annot["preferred"] = preferred_transcript
                main_annot = annot
                continue

            if main_annot is None:
                canonical = current_canonical
                consequence_score = current_consequence_score
                refseq = current_refseq
                protein_coding = current_protein_coding
                preferred_transcript = current_preferred_transcript
                annot["preferred"] = preferred_transcript
                main_annot = annot
                continue
        omims = Omim.query.filter(or_(Omim.geneSymbols.contains([main_annot["SYMBOL"]]), Omim.approvedGeneSymbol==main_annot["SYMBOL"])).all()
        phenotypes = list()
        for omim in omims:
            for pheno in omim.phenotypes:
                phenotypes.append({
                    "id": pheno.id,
                    "phenotypeMimNumber": pheno.phenotypeMimNumber,
                    "phenotype": pheno.phenotype,
                    "inheritances": str(pheno.inheritances),
                    "phenotypeMappingKey": pheno.phenotypeMappingKey
                })

        members = []
        os={}
        t={}
        if sample.patient:
            for s in sample.patient.samples:
                if s != sample:
                    members.append(str(s))
            if sample.patient.familyid:
                request_family = Patient.query.outerjoin(Sample).outerjoin(Var2Sample)\
                                .filter(and_(Var2Sample.variant_ID == variant.id, Patient.id != sample.patient.id))
                for member in request_family.all():
                    members.append(str(member))
            for s in sample.patient.samples:
                if s.status > 0 and s != sample:
                    os[str(s)]= dict()
                    req = Var2Sample.query.get((var2sample.variant_ID, s.id))
                    if req:
                        os[str(s)] = {
                            "depth": f"{req.depth}",
                            "allelic_depth": f"{req.allelic_depth}",
                            "allelic_frequency": f"{(req.allelic_depth / req.depth):.4f}",
                        }
                    else:
                        os[str(s)] = {
                            "depth": f"NA",
                            "allelic_depth": f"NA",
                            "allelic_frequency": f"NA",
                        }
            if sample.patient.familyid is not None:
                for p in sample.patient.family.patients:
                    if p == sample.patient:
                        continue
                    for s in p.samples:
                        if s.status < 1:
                            continue
                        t[str(s)]= dict()
                        req = Var2Sample.query.get((var2sample.variant_ID, s.id))
                        if req:
                            t[str(s)] = {
                                "depth": f"{req.depth}",
                                "allelic_depth": f"{req.allelic_depth}",
                                "allelic_frequency": f"{(req.allelic_depth / req.depth):.4f}",
                            }
                        else:
                            t[str(s)] = {
                                "depth": f"NA",
                                "allelic_depth": f"NA",
                                "allelic_frequency": f"NA",
                            }

        allelic_frequency = var2sample.allelic_depth / var2sample.depth

        null = Var2Sample.query.outerjoin(Sample, Var2Sample.sample).filter(and_(Var2Sample.variant == variant, Sample.patient_id == None)).count()
        not_null = Var2Sample.query.outerjoin(Sample, Var2Sample.sample).filter(and_(Var2Sample.variant == variant, Sample.patient_id != None, Sample.patient_id != sample.patient_id)).distinct(Sample.patient_id).count()

        variants["data"].append({
            "annotations": main_annot,
            "chr": f"{variant.chr}",
            "clinvar": {
                "VARID" : variant.clinvar_VARID,
                "CLNSIG" : variant.clinvar_CLNSIG,
                "CLNSIGCONF" : variant.clinvar_CLNSIGCONF,
                "CLNREVSTAT" : variant.clinvar_CLNREVSTAT
            },
            "id": f"{variant.id}",
            "pos": f"{variant.pos}",
            "ref": f"{variant.ref}",
            "alt": f"{variant.alt}",
            "filter": var2sample.filter,
            "depth": f"{var2sample.depth}",
            "reported": var2sample.reported,
            "class_variant": variant.class_variant,
            "allelic_depth": f"{var2sample.allelic_depth}",
            "allelic_frequency": f"{allelic_frequency:.4f}",
            "inseal": {
                "occurrences": null+not_null,
            },
            "phenotypes": phenotypes,
            "family": t,
            "os": os,
        })
    # print(variants)
    return jsonify(variants)


@app.route("/json/transcripts", methods=['GET', 'POST'])
@login_required
def json_transcripts():
    """
    Endpoint for retrieving all transcripts.

    Returns:
        A JSON object with the following properties:
        - recordsTotal: the total number of records in the database.
        - recordsFiltered: the number of records that match the current search
                           parameters.
        - data: a list of objects representing the transcripts data, with the
                following properties:
          - feature: the name of the feature.
          - biotype: the type of the feature.
          - feature_type: the type of the feature as specified by the source.
          - symbol: the gene symbol.
          - symbol_source: the source of the gene symbol.
          - gene: the gene name.
          - source: the source of the feature.
          - protein: the protein product of the transcript.
          - canonical: a flag indicating whether this transcript is the
                       canonical transcript of its gene.
          - hgnc: the HGNC identifier for the gene.
          - val: a boolean indicating whether the current user has this
                 transcript in their list of favorites.
    """
    key_list = {
        "asc": [
            Transcript.feature.asc(),
            Transcript.biotype.asc(),
            Transcript.feature_type.asc(),
            Transcript.symbol.asc(),
            Transcript.symbol_source.asc(),
            Transcript.gene.asc(),
            Transcript.source.asc(),
            Transcript.protein.asc(),
            Transcript.canonical.asc(),
            Transcript.hgnc.asc()
        ],
        "desc": [
            Transcript.feature.desc(),
            Transcript.biotype.desc(),
            Transcript.feature_type.desc(),
            Transcript.symbol.desc(),
            Transcript.symbol_source.desc(),
            Transcript.gene.desc(),
            Transcript.source.desc(),
            Transcript.protein.desc(),
            Transcript.canonical.desc(),
            Transcript.hgnc.desc()
        ]
    }
    filters = or_(
        Transcript.feature.op('~')(request.form['search[value]']),
        Transcript.biotype.op('~')(request.form['search[value]']),
        Transcript.feature_type.op('~')(request.form['search[value]']),
        Transcript.symbol.op('~')(request.form['search[value]']),
        Transcript.symbol_source.op('~')(request.form['search[value]']),
        Transcript.gene.op('~')(request.form['search[value]']),
        Transcript.source.op('~')(request.form['search[value]']),
        Transcript.protein.op('~')(request.form['search[value]']),
        Transcript.canonical.op('~')(request.form['search[value]']),
        Transcript.hgnc.op('~')(request.form['search[value]'])
    )

    transcripts = Transcript.query
    recordsTotal = transcripts.count()
    transcripts_filter = transcripts.filter(filters)
    recordsFiltered = transcripts_filter.count()
    transcripts = transcripts_filter\
        .order_by(key_list[request.form['order[0][dir]']][int(request.form['order[0][column]'])])\
        .offset(request.form["start"])\
        .limit(request.form["length"])\
        .all()
    transcripts_json = {
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": list()
    }

    for transcript in transcripts:
        t = False
        if transcript.feature in current_user.transcripts:
            t = True
        transcripts_json["data"].append({
            "feature": transcript.feature,
            "biotype": transcript.biotype,
            "feature_type": transcript.feature_type,
            "symbol": transcript.symbol,
            "symbol_source": transcript.symbol_source,
            "gene": transcript.gene,
            "source": transcript.source,
            "protein": transcript.protein,
            "canonical": transcript.canonical,
            "hgnc": transcript.hgnc,
            "val": t
        })
    return jsonify(transcripts_json)


@app.route("/json/filter/<int:id>")
@login_required
def json_filter(id=1):
    """
    Endpoint for retrieving a filter given its ID.

    Args:
        id (int): The ID of the filter to be returned.

    Returns:
        The JSON representation of the filter with the given ID.
    """
    filter = Filter.query.get(int(id))
    if not filter:
        flash(f"Filter '{id}' not found! Please contact admin!",
              category="error")
        return redirect(url_for('index'))

    return jsonify(filter.filter)


@app.route("/json/filters")
@login_required
def json_filters():
    """
    Endpoint for retrieving all filters that the current user has access to.

    Returns:
        A JSON object with the following properties:
        - ID of filter: filter name
    """
    filters = Filter.query.all()
    filter = dict()
    if filters:
        for f in filters:
            if bool(set(current_user.teams) & set(f.teams)) or not f.teams:
                filter[f.id] = f.filtername
    return jsonify(filter)


@app.route("/json/beds")
@login_required
def json_beds():
    """
    Endpoint for retrieving all beds that the current user has access to.

    Returns:
        A JSON object with the following properties:
        - ID of bed: bed name
    """
    beds = Bed.query.all()
    bed = dict()
    if beds:
        for b in beds:
            if bool(set(current_user.teams) & set(b.teams)) or not b.teams:
                bed[b.id] = b.name
    return jsonify(bed)


@app.route("/json/bed/<int:id>")
@login_required
def json_bed(id):
    """
    Endpoint for retrieving a bed given its ID.

    Args:
        id (int): The ID of the bed to be returned.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing a variant associated
                with the sample.
            Each dictionary has the following keys:
            - chr: The chromosome where the region is located.
            - start: The position where the region start.
            - stop: The position where the region stop.
            - name: The name of the region.
    """
    bed = Bed.query.get(int(id))
    data = list()
    if not bed:
        return jsonify({"data": data})
    for region in bed.regions:
        data.append({
            "chr": region.chr,
            "start": region.start,
            "stop": region.stop,
            "name": region.name,
        })
    return jsonify({"data": data})


@app.route("/json/history/<string:type>/<int:id>")
@app.route("/json/history/")
@login_required
def json_history(type=None, id=None):
    """
    Endpoint for retrieving the history of either a sample or a user.

    Args:
        type (str): The type of history to be returned, either "sample" or
                    "user".
        id (int): The ID of the sample or user to retrieve history for.

    Returns:
        A JSON object with the following keys:
        - data: A list of dictionaries, each representing an action
            Each dictionary has the following keys:
            - user: The username of the user that have done the action.
            - sample: The username of the sample that is concerned by the
                      action.
            - action: The action made.
            - date: The date and time that the action was made
                    (formatted as "YYYY/MM/DD HH:MM:SS").
    """
    if type == "sample":
        historics = History.query.filter_by(sample_ID= id)
    elif type == "user":
        historics = History.query.filter_by(user_ID= id)
    else:
        historics = History.query.all()
    historics_list = list()
    for history in historics:
        historics_list.append({
            "user": history.user.username,
            "sample": history.sample.samplename,
            "action": history.action,
            "date": history.date.strftime("%Y/%m/%d %H:%M:%S")
        })

    return jsonify({"data":historics_list})


@app.route("/json/variant/<string:id>")
@app.route("/json/variant/<string:id>/sample/<int:sample>")
@app.route("/json/variant/<string:id>/version/<int:version>")
@app.route("/json/variant/<string:id>/sample/<int:sample>/version/<int:version>")
@login_required
def json_variant(id, version=-1, sample=None):
    """
    Endpoint for retrieving a variant.

    Args:
        id (str): The ID of the variant to be returned.
        version (int): The version of the variant to be returned.
                       Defaults to the latest version.
        sample (int): The ID of the sample to retrieve variant information for.
                      Defaults to None.

    Returns:
        A JSON object with the following keys:
                        variant.
        - id: The identifier of the variant.
        - chr: The chromosome where the variant is located.
        - pos: The position of the variant.
        - ref: The reference sequence for the variant.
        - alt: The alternate sequence for the variant.
        - annotations: A dictionary containing the main annotation for the
        - samples: A list of dictionaries, each representing a sample
            Each dictionary has the following keys:
            - samplename: the name of the sample
            - affected: A boolean indicating the sample is affected
            - family: the family of the sample
            - current_family: A boolean indicating if this is the current
                              sample family
            - current: A boolean indicating if this is the current sample
            - depth: The sequencing depth of the variant in the sample.
            - allelic_depth: The allelic depth of the variant in the sample.
            - allelic_frequency: The allelic frequency of the variant in the
                                 sample.
            - reported: A boolean indicating whether the variant was reported
                        in the sample.
        - comments: A list of dictionaries, each representing a comment
            Each dictionary has the following keys:
            - comment: The text of the comment.
            - date: The date and time that the comment was posted
                    (formatted as "YYYY/MM/DD HH:MM:SS").
            - user: The username of the user that have done the action.
    """
    variant = Variant.query.get(id)
    if sample is not None:
        sample = Sample.query.get(sample)

    samples = list()
    for v2s in variant.samples:
        current_family = False
        current_patient = False
        current = False
        if v2s.sample.status >= 1:
            if (sample and sample.patient and v2s.sample.patient and v2s.sample.patient.familyid == sample.patient.familyid 
                    and sample.patient.familyid is not None):
                current_family = True
            if (sample and sample.patient and v2s.sample.patient and v2s.sample.patient_id == sample.patient_id):
                current_patient = True
            if sample and v2s.sample.id == sample.id:
                current = True
            allelic_frequency = v2s.allelic_depth / v2s.depth
            samples.append({
                "patient": {
                    "id": v2s.sample.patient_id,
                    "alias": v2s.sample.patient.alias if v2s.sample.patient else None
                },
                "samplename": v2s.sample.samplename,
                "affected": v2s.sample.patient.affected,
                "family": v2s.sample.patient.family.family if (v2s.sample.patient and v2s.sample.patient.family) else "",
                "current_family": current_family,
                "current_patient": current_patient,
                "teams": [{"teamname": t.teamname, "color": t.color} for t in v2s.sample.teams],
                "current": current,
                "depth": v2s.depth,
                "allelic_depth": v2s.allelic_depth,
                "allelic_frequency": f"{allelic_frequency:.4f}",
                "reported": v2s.reported
            })

    comments = list()

    for comment in variant.comments:
        comments.append({
            "comment": comment.comment,
            "date": comment.date.strftime("%Y/%m/%d at %H:%M:%S"),
            "user": comment.user.username
        })

    variant_json = {
        "id": variant.id,
        "chr": variant.chr,
        "pos": variant.pos,
        "ref": variant.ref,
        "alt": variant.alt,
        "annotations": variant.annotations[version],
        "samples": samples,
        "comments": comments
    }
    return jsonify(variant_json)


@app.route("/edit/sample/name", methods=['POST'])
@login_required
def edit_name():
    """
    Edits the name of a sample.

    This function handles a POST request to edit the name of a sample. It gets
    the new name from the request's form data and updates the `samplename`
    field of the sample in the database. It also creates a new `History`
    record in the database to log the action.

    Returns:
        str: "No Changes" if the new name is the same as the old name, "ok" if
             the update was successful.

    Raises:
        InvalidAPIUsage: If the new name is less than 2 or more than 20
                         characters long.
    """
    sample_id = request.form["sample_id"]
    new_name = request.form["new_name"]
    sample = Sample.query.get(sample_id)
    if sample.samplename == new_name:
        return "No Changes"
    old_name = sample.samplename
    if len(new_name) < 2 or len(new_name) > 20:
        raise InvalidAPIUsage("The samplename must be between 2 and 20 characters long.")

    sample.samplename = new_name
    history = History(sample_ID=sample_id, user_ID=current_user.id, date=datetime.now(), action=f"Sample rename : '{old_name}' -> '{sample.samplename}")
    db.session.add(history)
    db.session.commit()

    return "ok"


@app.route("/edit/sample/family", methods=['POST'])
@login_required
def edit_family():
    """
    Edits the family associated to a sample.

    This function handles a POST request to edit the family associated to a
    sample. It gets the new name family from the request's form data and
    updates the `family` field of the sample in the database. It also creates a
    new `History` record in the database to log the action.

    Returns:
        str: "No Changes" if the new name is the same as the old name, "ok" if
             the update was successful.

    Raises:
        InvalidAPIUsage: If the family name is less than 2 or more than 20
                         characters long.
    """
    sample_id = request.form["sample_id"]
    new_family = request.form["new_family"]
    sample = Sample.query.get(sample_id)

    if not new_family and sample.patient and sample.patient.familyid:
        history = History(sample_ID=sample_id, user_ID=current_user.id, date=datetime.now(), action=f"Family removed : '{sample.patient.family.family}' (id: {sample.patient.familyid})")
        sample.patient.familyid = None
    elif (not new_family and not sample.patient.family) or (sample.patient.family and sample.patient.family.family == new_family):
        return "ok"
    else:
        family = Family.query.filter(Family.family == new_family).first()
        if not family:
            family = Family(family=new_family)
            db.session.add(family)
            db.session.commit()
            history = History(sample_ID=sample_id, user_ID=current_user.id, date=datetime.now(), action=f"New Family created : '{family.family}' (id: {family.id})")
            db.session.add(history)
        if sample.patient and sample.patient.family:
            history = History(sample_ID=sample_id, user_ID=current_user.id, date=datetime.now(), action=f"Family linked : '{sample.patient.family.family}' (id: {sample.patient.familyid}) -> '{family.family}' (id: {family.id})")
        else:
            history = History(sample_ID=sample_id, user_ID=current_user.id, date=datetime.now(), action=f"Family linked : '{family.family}' (id: {family.id})")
        sample.patient.familyid = family.id

    db.session.add(history)
    db.session.commit()

    return "ok"


###############################################################################


###############################################################################
# Toggle boolean variables in DB

@app.route("/toggle/samples/variant/status", methods=['POST'])
@login_required
def toggle_varStatus():
    """
    Toggles the reported status of a variant to a sample.

    Returns:
        str: The new reported status of the variant.
    """
    id_var = request.form["id_var"]
    sample_id = request.form["sample_id"]
    v2s = Var2Sample.query.get((id_var, sample_id))
    v2s.reported = False if v2s.reported else True
    return_value = v2s.reported
    db.session.commit()

    report = "Report" if v2s.reported else "Unreport"
    history = History(
        sample_ID=sample_id,
        user_ID=current_user.id,
        date=datetime.now(),
        action=f"{report} variant : {id_var}")
    db.session.add(history)
    db.session.commit()

    return f"{return_value}"


@app.route("/toggle/samples/variant/hide", methods=['POST'])
@login_required
def toggle_varhide():
    """
    Toggles the hide status of a variant to a sample.

    Returns:
        str: The new hide status of the variant.
    """
    id_var = request.form["id_var"]
    sample_id = request.form["sample_id"]
    v2s = Var2Sample.query.get((id_var, sample_id))
    v2s.hide = not v2s.hide
    return_value = v2s.hide
    db.session.commit()

    report = "Hide" if v2s.hide else "Show"
    history = History(
        sample_ID=sample_id,
        user_ID=current_user.id,
        date=datetime.now(),
        action=f"{report} variant : {id_var}")
    db.session.add(history)
    db.session.commit()

    return f"{return_value}"


@app.route("/toggle/samples/variant/hide/all", methods=['POST'])
@login_required
def toggle_varhideall():
    """
    Toggles the hide status of all variant to a sample.

    Returns:
        str: The array of unhide variants
    """
    var_hide=list()
    sample_id = request.form["sample_id"]
    for v2s in Sample.query.get(sample_id).variants:
        if not v2s.hide:
            continue
        v2s.hide = not v2s.hide
        return_value = v2s.hide
        var_hide.append(str(v2s))
        db.session.commit()

        report = "Hide" if v2s.hide else "Show"
        history = History(
            sample_ID=sample_id,
            user_ID=current_user.id,
            date=datetime.now(),
            action=f"{report} variant : {v2s.variant_ID}")
        db.session.add(history)
        db.session.commit()

    return f"{str(return_value)}"


@app.route("/toggle/sample/index", methods=['POST'])
@login_required
def toggle_sampleIndex():
    """
    Toggles the index status of a sample.

    Returns:
        str: A message indicating the toggle was successful.
    """
    sample_id = request.form["sample_id"]
    sample = Sample.query.get(sample_id)
    old = sample.patient.index
    sample.patient.index = False if sample.patient.index else True

    history = History(
        sample_ID=sample.id, 
        user_ID=current_user.id, 
        date=datetime.now(), 
        action=f"Toggle index : '{str(old)}' -> '{str(sample.patient.index)}'")
    db.session.add(history)
    db.session.commit()

    return "ok"


@app.route("/toggle/sample/affected", methods=['POST'])
@login_required
def toggle_sampleAffected():
    """
    Toggles the affected status of a sample.

    Returns:
        str: A message indicating the toggle was successful.
    """
    sample_id = request.form["sample_id"]
    sample = Sample.query.get(sample_id)
    old = sample.patient.affected
    sample.patient.affected = False if sample.patient.affected else True

    history = History(
        sample_ID=sample.id, 
        user_ID=current_user.id, 
        date=datetime.now(), 
        action=f"Toggle affected : '{str(old)}' -> '{str(sample.patient.affected)}'")
    db.session.add(history)
    db.session.commit()

    return "ok"


@app.route("/toggle/sample/filter", methods=['POST'])
@login_required
def toggle_sampleFilter():
    """
    Toggles the filter of a sample.

    Returns:
        str: The ID of the new filter.
    """
    sample_id = request.form["id_sample"]
    filter_id = request.form["id_filter"]
    sample = Sample.query.get(sample_id)
    old_filter = sample.filter
    sample.filter_id = filter_id
    db.session.commit()

    if sample.filter != old_filter:
        history = History(
            sample_ID=sample.id,
            user_ID=current_user.id,
            date=datetime.now(),
            action=f"Change filter : '{str(old_filter)}' -> '{str(sample.filter)}'")
        db.session.add(history)
        db.session.commit()
    return escape(f"{sample.filter_id}")


@app.route("/toggle/sample/panel", methods=['POST'])
@login_required
def toggle_samplePanel():
    """
    Toggles the panel of a sample.

    Returns:
        str: The ID of the new panel.
    """
    sample_id = request.form["id_sample"]
    panel_id = request.form["id_panel"] if "id_panel" in request.form and int(request.form["id_panel"]) > 0 else None
    sample = Sample.query.get(sample_id)
    old_bed = sample.bed
    sample.bed_id = panel_id
    db.session.commit()

    if sample.bed != old_bed:
        history = History(
            sample_ID=sample.id,
            user_ID=current_user.id,
            date=datetime.now(),
            action=f"Change panel : '{str(old_bed)}' -> '{str(sample.bed)}'")
        db.session.add(history)
        db.session.commit()

    count_hide=0

    for v in  Var2Sample.query.filter(Var2Sample.sample_ID == sample.id, Var2Sample.hide == True):
        if v.inBed():
            count_hide+=1

    return escape(count_hide)


@app.route("/toggle/samples/variant/class", methods=['POST'])
@login_required
def toggle_varClass():
    """
    Toggles the class of a variant.

    Returns:
        str: The new class of the variant.
    """
    id_var = request.form["id_var"]
    class_variant = request.form["class_variant"]
    variant = Variant.query.get(id_var)
    variant.class_variant = class_variant
    db.session.commit()
    return escape(f"{variant.class_variant}")


@app.route("/toggle/sample/status", methods=['POST'])
@login_required
def toggle_sampleStatus():
    """
    Toggles the status of a sample.

    Returns:
        str: A message indicating the toggle was successful.
    """
    sample_id = request.form["sample_id"]
    sample = Sample.query.get(sample_id)
    status = int(request.form["status"]) if "status" in request.form else False
    old_status = sample.status

    if status:
        if not(status == 4 and not (current_user.biologist or current_user.admin)):
            sample.status = request.form["status"]
            db.session.commit()
    elif sample.status == 1:
        sample.status = 2
        db.session.commit()

    status_dict = {
        -1: "Error",
        0: "Importing",
        1: "New Sample",
        2: "Processing",
        3: "Interpreted",
        4: "Validated"
    }

    if sample.status != old_status:
        history = History(
            sample_ID=sample.id,
            user_ID=current_user.id, date=datetime.now(),
            action=f"Status : '{status_dict[old_status]}' -> '{status_dict[sample.status]}'")
        db.session.add(history)
        db.session.commit()
    return escape(f"{sample} - {sample.status}")


@app.route("/add/comment/variant", methods=['POST'])
@login_required
def add_comment_variant():
    """
    Adds a comment to a variant.

    Returns:
        str: A message indicating the comment was added.
    """
    comment = Comment_variant(
        comment=urllib.parse.unquote(request.form["comment"]),
        variantid=request.form["id"],
        date=datetime.now(),
        userid=current_user.id)
    db.session.add(comment)
    db.session.commit()
    return 'ok'


@app.route("/add/comment/sample", methods=['POST'])
@login_required
def add_comment_sample():
    """
    Adds a comment to a sample.

    Returns:
        str: A message indicating the comment was added.
    """
    comment = Comment_sample(
        comment=urllib.parse.unquote(request.form["comment"]),
        sampleid=request.form["id"],
        date=datetime.now(),
        userid=current_user.id)
    db.session.add(comment)
    db.session.commit()
    return 'ok'


@app.route("/add/filter", methods=['POST'])
@login_required
def add_filter():
    """
    Add or edit a filter.

    Returns:
        str: A message indicating the filter was added.
    """

    if request.form["edit"] == "true":
        filter = Filter.query.get(request.form["id"])
        filter.filter = json.loads(request.form["filter"])
        db.session.commit()
    else:
        teams = list()
        for name in json.loads(request.form['teams']):
            teams.append(Team.query.filter_by(teamname=name).first())
        filter = Filter(
            filtername=urllib.parse.unquote(request.form["name"]),
            filter=json.loads(request.form["filter"]),
            teams=teams
        )
        try:
            db.session.add(filter)
            db.session.commit()
        except IntegrityError as e:
            assert isinstance(e.orig, UniqueViolation)  # proves the original exception
            return "This filter name already exist!", 500
    return 'ok'


@app.route("/add/preferred", methods=['POST'])
@login_required
def add_preferred():
    """
    Adds or removes a transcript to/from the current user's list of preferred
    transcripts.

    Returns:
        str: Returns the string 'ok' if the operation was successful.
    """
    user = User.query.filter_by(id=current_user.get_id()).first()

    transcript = urllib.parse.unquote(request.form["transcript"])
    # transcript = Transcript.query.get(transcript_id)
    if transcript in user.transcripts:
        user.transcripts.remove(transcript)
    else:
        user.transcripts.append(transcript)
    db.session.commit()
    return 'ok'


@app.route("/toggle/user/sidebar", methods=['POST'])
@login_required
def toggle_user_sidebar():
    """
    Toggles the current user's sidebar status (open or closed).

    Returns:
        str: Returns the string 'OK' if the operation was successful.
    """
    current_user.sidebar = (not current_user.sidebar)
    db.session.commit()
    return "OK"

# from anacore.vcf import VCFIO, VCFRecord, HeaderInfoAttr, HeaderFormatAttr
# import tempfile

# @app.route("/variants/all/vcf")
# def get_variant_vcf():
#     """
#     Send variant into vcf.

#     Returns:
#         str: Returns all variants into a vcf file.
#     """
#     handle, filepath = tempfile.mkstemp(suffix=".vcf.gz")
#     with VCFIO(filepath, "w") as writer:
#         writer.samples = ["my_sample"]
#         writer.extra_header = [
#             "##source=seal",
#         ]
#         writer.info = {
#             "DB": HeaderInfoAttr("DB", "dbSNP membership, build 129", "Flag", 0)
#         }
#         writer.format = {
#             "AF": HeaderFormatAttr("AF", "Allele Frequency", "Float", "A")
#         }
#         writer.writeHeader()
#         writer.writer(VCFRecord("chr3", "12", '', "A", "T", 30, ["PASS"], {'DB':'T'}, ["AF"], {"10"}))
#         # for record in vcf_record_list:
#         #     writer.write(record)
#     return send_file()

###############################################################################
