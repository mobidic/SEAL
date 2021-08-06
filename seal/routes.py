import os
import secrets
import json
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, jsonify
from seal import app, db, bcrypt
from seal.forms import LoginForm, UpdateAccountForm, UpdatePasswordForm, UploadVariantForm, SelectFilterForm
from seal.models import User, Sample, Filter, Transcript
from flask_login import login_user, current_user, logout_user, login_required


################################################################################
# Essentials pages


@app.route("/")
@app.route("/home")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    return render_template(
        "essentials/home.html",
        title="Home"
    )


@app.route("/about")
def about():
    return render_template(
        "essentials/about.html",
        title="About"
    )


@app.route("/contact")
def contact():
    return render_template(
        "essentials/contact.html",
        title="Contact"
    )


################################################################################


################################################################################
# Authentication


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            flash(f'You are logged as: {user.username}!', 'success')
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsucessful. Please check the username and/or password!', 'error')
    return render_template(
        "authentication/login.html",
        title="Login",
        form=form
    )


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images/profile', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    flash("You have been disconnected!", "warning")
    return redirect(url_for('index'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    update_account_form = UpdateAccountForm()
    update_password_form = UpdatePasswordForm()
    if "submit_update" in request.form and update_account_form.validate_on_submit():
        if update_account_form.image_file.data:
            picture_file = save_picture(update_account_form.image_file.data)
            current_user.image_file = picture_file

        current_user.mail = update_account_form.mail.data
        current_user.username = update_account_form.username.data
        db.session.commit()

        flash('Your account has been updated!', 'success')
    elif "submit_password" in request.form and update_password_form.validate_on_submit():
        current_user.password = bcrypt.generate_password_hash(update_password_form.new_password.data).decode('utf-8')
        db.session.commit()

        flash('Your password has been changed!', 'success')

    update_account_form.username.data = current_user.username
    update_account_form.mail.data = current_user.mail

    return render_template(
        'authentication/account.html', title='Account',
        update_account_form=update_account_form,
        update_password_form=update_password_form)


################################################################################


################################################################################
# Analysis


@app.route("/sample/<int:id>", methods=['GET', 'POST'])
@login_required
def sample(id):
    sample = Sample.query.get(int(id))
    if not sample:
        flash(f"Error sample not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    filters = list()
    for filter in Filter.query.all():
        if current_user.filter_id == filter.id:
            filters.append((filter.id, f'{filter.filtername} (default)'))
        else:
            filters.append((filter.id, f'{filter.filtername}'))

    selectFilterForm = SelectFilterForm()
    selectFilterForm.filter.choices = filters
    if "submit_filter" in request.form and selectFilterForm.validate_on_submit():
        filter = Filter.query.get(selectFilterForm.filter.data)
        flash(f"You are using '{filter.filtername}' as filter!", 'warning')
    else:
        filter = Filter.query.get(current_user.filter_id)

    return render_template(
        'analysis/sample.html', title=f'{sample.samplename}',
        selectFilterForm=selectFilterForm,
        sample=sample,
        filter=filter
    )


@app.route("/json/samples", methods=['GET', 'POST'])
@login_required
def samples():
    samples = db.session.query(Sample.id, Sample.samplename, Sample.status).all()
    samples_json = {"data": list()}
    for sample in samples:
        samples_json["data"].append({
            "id": sample[0],
            "samplename": sample[1],
            "status": sample[2]
        })
    return jsonify(samples_json)


@app.route("/json/variants/sample/<int:id>", methods=['GET', 'POST'])
@app.route("/json/variants/sample/<int:id>/version/<int:version>", methods=['GET', 'POST'])
@login_required
def variants(id, version=-1):
    sample = Sample.query.get(int(id))
    if not sample:
        flash(f"Error sample not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    variants = {"data": list()}
    for variant in sample.variants:
        try:
            annotations = variant.annotations[-1]["ANN"]
        except TypeError:
            annotations = None
        variants["data"].append({
            "chr": f"{variant.chr}",
            "pos": f"{variant.pos}",
            "ref": f"{variant.ref}",
            "alt": f"{variant.alt}",
            "annotations": f"{annotations}",
        })

    return jsonify(variants)


@app.route("/json/transcripts")
@login_required
def transcripts():
    transcripts = db.session.query(Transcript).all()
    transcripts_json = {"data": list()}
    print(transcripts)
    for transcript in transcripts:
        # for transcript in gene.transcripts:
        transcripts_json["data"].append({
            "hgncname": transcript.gene.hgncname,
            "hgncid": transcript.gene.hgncid,
            "chromosome": transcript.gene.chromosome,
            "strand": transcript.gene.strand,
            "refSeq": transcript.refSeq,
            "canonical": transcript.canonical,
            "refProt": transcript.refProt,
            "uniprot": transcript.uniprot
        })
    return jsonify(transcripts_json)


def add_vcf(samplename, vcf_file):
    random_hex = secrets.token_hex(8)

    _, f_ext = os.path.splitext(vcf_file.filename)

    vcf_fn = random_hex + f_ext
    vcf_path = os.path.join(app.root_path, 'static/temp/vcf/', vcf_fn)
    vcf_file.save(vcf_path)

    token_fn = random_hex + ".token"
    token_path = os.path.join(app.root_path, 'static/temp/vcf/', token_fn)
    with open(token_path, "w") as tf:
        tf.write(json.dumps({
            "samplename": samplename
        }))

    return vcf_fn


@app.route("/create/sample", methods=['GET', 'POST'])
@login_required
def create_variant():
    uploadSampleForm = UploadVariantForm()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if "submit" in request.form and uploadSampleForm.validate_on_submit():
        sample = Sample.query.filter_by(samplename=uploadSampleForm.samplename.data).first()
        if sample:
            flash("This Sample Name is already in database!", "error")
            return redirect(url_for('index'))

        add_vcf(uploadSampleForm.samplename.data, uploadSampleForm.vcf_file.data)

        flash(f'The sample {uploadSampleForm.samplename.data} will be added soon!', 'info')
        return redirect(url_for('index'))

    return render_template(
        'analysis/create_sample.html', title="Add Sample",
        form=uploadSampleForm
    )
