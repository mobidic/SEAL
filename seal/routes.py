from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import functools
import json
import secrets
import urllib

from PIL import Image
from flask import (flash, jsonify, redirect, render_template, request, url_for,
                   send_file)
from flask_login import current_user, login_user, logout_user
from flask_login.utils import EXEMPT_METHODS
from flask_wtf.csrf import CSRFError
from sqlalchemy import and_, or_

from seal import app, bcrypt, db
from seal.forms import (AddCommentForm, LoginForm, SaveFilterForm,
                        UploadPanelForm, UploadVariantForm,
                        UpdateAccountForm, UpdatePasswordForm)
from seal.models import (Bed, Comment_sample, Comment_variant, Family, Filter,
                         History, Omim, Region, Run, Sample, Team,
                         Transcript, User, Variant, Var2Sample)


###############################################################################
# Decorators/Exceptions and handler


# Here define safe host authorized for a redirection
SAFE_HOST = []


def redirect_dest(fallback):
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
    url = urlparse(dest)
    if url.path and not url.netloc:
        return redirect(url.path)
    if url.hostname and url.hostname in SAFE_HOST:
        return redirect(url.geturl())
    else:
        flash(f"Redirection to '{url.hostname}' forbidden !", "error")
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
    return redirect(url_for('index'))


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(405)
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
            return redirect_dest(fallback=url_for('index'))
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
        return redirect_dest(fallback=url_for('index'))
    if ("submit_password" in request.form 
            and update_password_form.validate_on_submit()):
        pwd = update_password_form.new_password.data
        current_user.password = bcrypt.generate_password_hash(pwd).decode('utf-8')
        current_user.logged = True
        db.session.commit()
        flash('Your password has been changed!', 'success')
        return redirect_dest(fallback=url_for('index'))

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

    return render_template(
        'analysis/sample.html', title=f'{sample.samplename}',
        sample=sample,
        form=commentForm,
        saveFilterForm=saveFilterForm
    )


@app.route("/create/sample", methods=['GET', 'POST'])
@login_required
def create_variant():
    """
    View function for creating a new sample variant.

    If the form is submitted, adds the variant information and uploaded VCF to
    the database and returns to the index page.
    If the form is not submitted, displays the upload form.

    Returns:
        A rendered template of the upload variant form.
    """
    uploadSampleForm = UploadVariantForm()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if "submit" in request.form and uploadSampleForm.is_submitted():
        run = Run.query.filter_by(name=uploadSampleForm.run.data).first()
        samplename = uploadSampleForm.samplename.data
        if run:
            sample = Sample.query.filter_by(samplename=samplename,
                                            runid=run.id).first()
        else:
            sample = Sample.query.filter_by(samplename=samplename,
                                            runid=None).first()
        if sample:
            flash("This Sample Name is already in database!", "error")
            return redirect(url_for('index'))

        info = {
            "samplename": uploadSampleForm.samplename.data,
            "affected": uploadSampleForm.affected.data,
            "index": uploadSampleForm.index.data,
            "userid": current_user.id,
            "date": str(datetime.now()),
            "family": {
                "name": uploadSampleForm.family.data
            },
            "run": {
                "name": uploadSampleForm.run.data,
            },
            "filter": {
                "name": uploadSampleForm.filter.data,
            },
            "bed": {
                "name": uploadSampleForm.bed.data,
            },
            "teams": [
                {"name": Team.query.get(id).teamname} for id in uploadSampleForm.teams.data
            ],
            "interface": True
        }
        add_vcf(info, uploadSampleForm.vcf_file.data)

        flash(f'Sample {uploadSampleForm.samplename.data} will be added soon!',
              'info')
        return redirect(url_for('index'))

    choices = [(team.id, team.teamname) for team in Team.query.all()]
    uploadSampleForm.teams.choices = choices
    uploadSampleForm.teams.data = [team.id for team in current_user.teams]

    return render_template(
        'analysis/create_sample.html', title="Add Sample",
        form=uploadSampleForm,
        user_teams=[team.teamname for team in current_user.teams]
    )


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
    families = db.session.query(Family.id, Family.family).all()
    families_json = {"data": list()}
    for family in families:
        families_json["data"].append({
            "id": family.id,
            "family": family.family
        })
    return jsonify(families_json)


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
    runs = db.session.query(Run.id, Run.name, Run.alias).all()
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
            - teams: a list of dictionaries, each containing the name and color
                     of a team associated with the sample
    """
    key_list = {
        "asc": [
            Sample.samplename.asc(),
            Family.family.asc(),
            Run.name.asc(),
            Run.alias.asc(),
            Sample.status.asc()
        ],
        "desc": [
            Sample.samplename.desc(),
            Family.family.desc(),
            Run.name.desc(),
            Run.alias.desc(),
            Sample.status.desc()
        ]
    }
    filters = or_(
        Sample.samplename.op('~')(request.form['search[value]']),
        Family.family.op('~')(request.form['search[value]']),
        Run.name.op('~')(request.form['search[value]']),
        Run.alias.op('~')(request.form['search[value]'])
    )

    if current_user.admin:
        samples = db.session.query(Sample)
    else:
        filter_samples_teams = or_(
            Sample.teams.any(Team.id.in_([t.id for t in current_user.teams])), 
            Sample.teams == None
        )
        samples = db.session.query(Sample).filter(filter_samples_teams)
    recordsTotal = samples.count()
    samples_filter = samples.outerjoin(Family, Sample.family)\
                            .outerjoin(Run, Sample.run).filter(filters)
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
            "family": sample.family.family if sample.familyid else None,
            "run": {
                "name": sample.run.name if sample.runid else None,
                "alias": sample.run.alias if sample.runid else None
            },
            "status": sample.status,
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

    var2samples = db.session.query(Var2Sample)\
                    .filter(Var2Sample.sample_ID == int(id))
    for var2sample in var2samples:
        variant = db.session.query(Variant)\
                    .filter(Variant.id == var2sample.variant_ID).first()
        try:
            if bed and not bed.varInBed(variant):
                continue
        except NameError:
            pass
        annotations = variant.annotations
        main_annot = None
        consequence_score = -999
        canonical = False
        refseq = False
        protein_coding = False
        preferred_transcript = False

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

        omims = Omim.query.filter_by(approvedGeneSymbol=main_annot["SYMBOL"])
        phenotypes = list()
        if omims.count():
            for omim in omims.all():
                for pheno in omim.phenotypes:
                    phenotypes.append({
                        "id": pheno.id,
                        "phenotypeMimNumber": pheno.phenotypeMimNumber,
                        "phenotype": pheno.phenotype,
                        "inheritances": str(pheno.inheritances),
                        "phenotypeMappingKey": pheno.phenotypeMappingKey
                    })
        cnt = db.session.query(Sample.samplename).outerjoin(Var2Sample) \
                .filter(and_(Sample.status >= 1, Sample.id != sample.id, 
                             Var2Sample.variant_ID == var2sample.variant_ID,
                             or_(Sample.teams == None,
                                 Sample.teams.any(Team.id.in_([t.id for t in sample.teams])),
                                 sample.teams == None))).count()
        total_samples = db.session.query(Sample) \
                          .filter(and_(Sample.status >= 1,
                                       Sample.id != sample.id,
                                       or_(Sample.teams == None,
                                           Sample.teams.any(Team.id.in_([t.id for t in sample.teams])),
                                           sample.teams == None ))).count()

        members = []
        if sample.familyid is None:
            cnt_family = None
        else:
            request_family = db.session.query(Sample.samplename).outerjoin(Var2Sample)\
                               .filter(and_(Sample.familyid == sample.familyid,
                                            Sample.status >= 1,
                                            Sample.id != sample.id,
                                            Var2Sample.variant_ID == var2sample.variant_ID))
            cnt_family = request_family.count()
            if cnt_family >= 0:
                for member in request_family:
                    members.append(member.samplename)

        allelic_frequency = var2sample.allelic_depth / var2sample.depth

        variants["data"].append({
            "annotations": main_annot,
            "chr": f"{variant.chr}",
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
                "occurrences": cnt,
                "total_samples": total_samples,
                "occurences_family": cnt_family,
                "family_members": members
            },
            "phenotypes": phenotypes
        })

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

    transcripts = db.session.query(Transcript)
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
@login_required
def json_history(type, id):
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
    if sample is None:
        s_teams = None
    else:
        sample = Sample.query.get(sample)
        s_teams = sample.teams

    samples = list()
    for v2s in variant.samples:
        current_family = False
        current = False
        if has_common_elements(s_teams, v2s.sample.teams):
            if v2s.sample.status >= 1:
                if (sample and v2s.sample.familyid == sample.familyid 
                        and sample.familyid is not None):
                    current_family = True
                if sample and v2s.sample.id == sample.id:
                    current = True
                allelic_frequency = v2s.allelic_depth / v2s.depth
                samples.append({
                    "samplename": v2s.sample.samplename,
                    "affected": v2s.sample.affected,
                    "family": v2s.sample.family.family if v2s.sample.family else "",
                    "current_family": current_family,
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
    old = sample.index
    sample.index = False if sample.index else True

    history = History(
        sample_ID=sample.id, 
        user_ID=current_user.id, 
        date=datetime.now(), 
        action=f"Toggle index : '{str(old)}' -> '{str(sample.index)}'")
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
    old = sample.affected
    sample.affected = False if sample.affected else True

    history = History(
        sample_ID=sample.id, 
        user_ID=current_user.id, 
        date=datetime.now(), 
        action=f"Toggle affected : '{str(old)}' -> '{str(sample.affected)}'")
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
    return f"{sample.filter_id}"


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

    return f"{sample.bed_id}"


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
    return f"{variant.class_variant}"


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
    return f"{sample} - {sample.status}"


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
    Adds a filter to the database.

    Returns:
        str: A message indicating the filter was added.
    """
    teams = list()
    for name in json.loads(request.form['teams']):
        teams.append(Team.query.filter_by(teamname=name).first())
    filter = Filter(
        filtername=urllib.parse.unquote(request.form["name"]),
        filter=json.loads(request.form["filter"]),
        teams=teams
    )
    db.session.add(filter)
    db.session.commit()
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
    user = db.session.query(User).filter_by(id=current_user.get_id()).first()

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
