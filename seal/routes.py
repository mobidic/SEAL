import os
import secrets
import json
import urllib
import functools
from datetime import datetime
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, jsonify
from seal import app, db, bcrypt
from seal.forms import LoginForm, UpdateAccountForm, UpdatePasswordForm, UploadVariantForm, AddCommentForm, SaveFilterForm
from seal.models import User, Sample, Filter, Transcript, Family, Variant, Var2Sample, Comment, Run
from flask_login import login_user, current_user, logout_user
from flask_login.utils import EXEMPT_METHODS
from sqlalchemy import or_, and_
################################################################################
# Define global variables
# TODO: create values in database

CONSEQUENCES_DICT = {
    "stop_gained": 20,
    "stop_lost": 20,
    "splice_acceptor_variant": 10,
    "splice_donor_variant": 10,
    "frameshift_variant": 10,
    "transcript_ablation": 10,
    "start_lost": 10,
    "transcript_amplification": 10,
    "missense_variant": 10,
    "protein_altering_variant": 10,
    "splice_region_variant": 10,
    "inframe_insertion": 10,
    "inframe_deletion": 10,
    "incomplete_terminal_codon_variant": 10,
    "stop_retained_variant": 10,
    "start_retained_variant": 10,
    "synonymous_variant": 10,
    "coding_sequence_variant": 10,
    "mature_miRNA_variant": 10,
    "intron_variant": 10,
    "NMD_transcript_variant": 10,
    "non_coding_transcript_exon_variant": 5,
    "non_coding_transcript_variant": 5,
    "3_prime_UTR_variant": 2,
    "5_prime_UTR_variant": 2,
    "upstream_gene_variant": 0,
    "downstream_gene_variant": 0,
    "TFBS_ablation": 0,
    "TFBS_amplification": 0,
    "TF_binding_site_variant": 0,
    "regulatory_region_ablation": 0,
    "regulatory_region_amplification": 0,
    "regulatory_region_variant": 0,
    "feature_elongation": 0,
    "feature_truncation": 0,
    "intergenic_variant": 0
}
GNOMADG = [
    "gnomADg_AF_AFR",
    "gnomADg_AF_AMR",
    "gnomADg_AF_ASJ",
    "gnomADg_AF_EAS",
    "gnomADg_AF_FIN",
    "gnomADg_AF_NFE",
    "gnomADg_AF_OTH"
]
ANNOT_TO_SPLIT = [
    "Existing_variation",
    "Consequence",
    "CLIN_SIG",
    "SOMATIC",
    "PHENO",
    "PUBMED"
]
MISSENSES = [
    "CADD_raw_rankscore_hg19",
    "VEST4_rankscore",
    "MetaSVM_rankscore",
    "MetaLR_rankscore",
    "Eigen-raw_coding_rankscore",
    "Eigen-PC-raw_coding_rankscore",
    "REVEL_rankscore",
    "BayesDel_addAF_rankscore",
    "BayesDel_noAF_rankscore",
    "ClinPred_rankscore"
]
SPLICEAI = [
    "AG",
    "AL",
    "DG",
    "DL"
]


def login_required(func):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
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


@app.route("/")
@app.route("/home")
@login_required
def index():
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


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(405)
@app.errorhandler(408)
@app.errorhandler(410)
@app.errorhandler(500)
def page_not_found(e):
    return render_template(
        "essentials/error.html",
        title=e.code, e=e
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
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not user.logged:
                return redirect(url_for('first_connexion', next=next_page))
            flash(f'You are logged as: {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsucessful. Please check the username and/or password!', 'error')
    return render_template(
        "authentication/login.html",
        title="Login",
        form=form
    )


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images/profile', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i = crop_max_square(i).resize(output_size, Image.LANCZOS)
    i.save(picture_path)

    return picture_fn


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    flash("You have been disconnected!", "warning")
    return redirect(url_for('login'))


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


@app.route("/first_connexion", methods=['GET', 'POST'])
@login_required
def first_connexion():
    update_password_form = UpdatePasswordForm()
    next_page = request.args.get('next')
    if current_user.logged:
        return redirect(next_page) if next_page else redirect(url_for('index'))
    if "submit_password" in request.form and update_password_form.validate_on_submit():
        current_user.password = bcrypt.generate_password_hash(update_password_form.new_password.data).decode('utf-8')
        current_user.logged = True
        db.session.commit()
        flash('Your password has been changed!', 'success')
        return redirect(next_page) if next_page else redirect(url_for('index'))

    return render_template(
        'authentication/first_connexion.html', title='First Connexion',
        update_password_form=update_password_form)


################################################################################


################################################################################
# Analysis


@app.route("/transcripts", methods=['GET', 'POST'])
@login_required
def transcripts():
    return render_template('analysis/transcripts.html', title='Transcripts',)


@app.route("/sample/<int:id>", methods=['GET', 'POST'])
@login_required
def sample(id):
    sample = db.session.query(Sample.samplename, Sample.id, Sample.familyid, Sample.status).filter(Sample.id == id).first()
    if not sample:
        flash(f"Error sample not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    commentForm = AddCommentForm()
    saveFilterForm = SaveFilterForm()

    return render_template(
        'analysis/sample.html', title=f'{sample.samplename}',
        sample=sample,
        form=commentForm,
        saveFilterForm=saveFilterForm
    )


def add_vcf(info, vcf_file):
    random_hex = secrets.token_hex(8)

    _, f_ext = os.path.splitext(vcf_file.filename)

    vcf_fn = random_hex + f_ext
    vcf_path = os.path.join(app.root_path, 'static/temp/vcf/', vcf_fn)
    vcf_file.save(vcf_path)

    info["vcf_path"] = vcf_path

    token_fn = random_hex + ".token"
    token_path = os.path.join(app.root_path, 'static/temp/vcf/', token_fn)
    with open(token_path, "w") as tf:
        tf.write(json.dumps(info))

    return vcf_fn


@app.route("/create/sample", methods=['GET', 'POST'])
@login_required
def create_variant():
    uploadSampleForm = UploadVariantForm()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if "submit" in request.form and uploadSampleForm.validate_on_submit():
        run = Run.query.filter_by(run_name=uploadSampleForm.run.data).first()
        if run:
            sample = Sample.query.filter_by(samplename=uploadSampleForm.samplename.data, runid=run.id).first()
        else:
            sample = Sample.query.filter_by(samplename=uploadSampleForm.samplename.data, runid=None).first()
        if sample:
            flash("This Sample Name is already in database!", "error")
            return redirect(url_for('index'))

        info = {
            "samplename": uploadSampleForm.samplename.data,
            "family": uploadSampleForm.family.data,
            "run": uploadSampleForm.run.data,
            "carrier": uploadSampleForm.carrier.data,
            "index": uploadSampleForm.index.data,
            "interface": True
        }
        add_vcf(info, uploadSampleForm.vcf_file.data)

        flash(f'The sample {uploadSampleForm.samplename.data} will be added soon!', 'info')
        return redirect(url_for('index'))

    return render_template(
        'analysis/create_sample.html', title="Add Sample",
        form=uploadSampleForm
    )


################################################################################


################################################################################
# JSON views

@app.route("/json/families", methods=['GET', 'POST'])
@login_required
def json_families():
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
    runs = db.session.query(Run.id, Run.run_name, Run.run_alias).all()
    runs_json = {"data": list()}
    for run in runs:
        runs_json["data"].append({
            "id": run.id,
            "run_name": run.run_name,
            "run_alias": run.run_alias
        })
    return jsonify(runs_json)


@app.route("/json/samples", methods=['GET', 'POST'])
@login_required
def json_samples():
    key_list = {
        "asc": [
            Sample.samplename.asc(),
            Family.family.asc(),
            Run.run_name.asc(),
            Run.run_alias.asc(),
            Sample.status.asc()
        ],
        "desc": [
            Sample.samplename.desc(),
            Family.family.desc(),
            Run.run_name.desc(),
            Run.run_alias.desc(),
            Sample.status.desc()
        ]
    }
    filters = or_(
        Sample.samplename.op('~')(request.form['search[value]']),
        Family.family.op('~')(request.form['search[value]']),
        Run.run_name.op('~')(request.form['search[value]']),
        Run.run_alias.op('~')(request.form['search[value]'])
    )

    samples = db.session.query(Sample)
    recordsTotal = samples.count()
    samples_filter = samples.outerjoin(Family, Sample.family).outerjoin(Run, Sample.run).filter(filters)
    recordsFiltered = samples_filter.count()
    samples = samples_filter.\
        order_by(key_list[request.form['order[0][dir]']][int(request.form['order[0][column]'])]).\
        offset(request.form["start"]).\
        limit(request.form["length"]).\
        all()
    samples_json = {
        "recordsTotal": recordsTotal,
        "recordsFiltered": recordsFiltered,
        "data": list()
    }

    for sample in samples:
        samples_json["data"].append({
            "id": sample.id,
            "samplename": sample.samplename,
            "family": sample.family.family if sample.familyid else None,
            "run": sample.run.run_name if sample.runid else None,
            "run_alias": sample.run.run_alias if sample.runid else None,
            "status": sample.status
        })
    return jsonify(samples_json)


@app.route("/json/variants/sample/<int:id>", methods=['GET', 'POST'])
@app.route("/json/variants/sample/<int:id>/version/<int:version>", methods=['GET', 'POST'])
@login_required
def json_variants(id, version=-1):
    sample = Sample.query.get(int(id))
    if not sample:
        flash(f"Error sample not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    variants = {"data": list()}

    # Get all canonical trancripts

    ##################################################

    var2samples = db.session.query(Var2Sample).filter(Var2Sample.sample_ID == int(id))
    for var2sample in var2samples:
        variant = db.session.query(Variant).filter(Variant.id == var2sample.variant_ID).first()
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
            # current_transcript = Transcript.query.get(annot['Feature'])
            # current_transcript = Transcript.query.get(annot['Feature'])
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

        cnt = db.session.query(Sample.samplename).outerjoin(Var2Sample).filter(and_(Sample.status >= 1, Sample.id != sample.id, Var2Sample.variant_ID == var2sample.variant_ID)).count()
        total_samples = db.session.query(Sample).filter(and_(Sample.status >= 1, Sample.id != sample.id)).count()
        if sample.familyid is None:
            cnt_family = None
        else:
            cnt_family = db.session.query(Sample.samplename).outerjoin(Var2Sample).filter(and_(Sample.familyid == sample.familyid, Sample.status >= 1, Sample.id != sample.id, Var2Sample.variant_ID == var2sample.variant_ID)).count()

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
                "occurences_family": cnt_family
            }
        })

    print(variants)
    return jsonify(variants)


@app.route("/json/transcripts", methods=['GET', 'POST'])
@login_required
def json_transcripts():
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
    transcripts = transcripts_filter.\
        order_by(key_list[request.form['order[0][dir]']][int(request.form['order[0][column]'])]).\
        offset(request.form["start"]).\
        limit(request.form["length"]).\
        all()
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
    filter = Filter.query.get(int(id))
    if not filter:
        flash(f"Error filter not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    return jsonify(filter.filter)


@app.route("/json/filters")
@login_required
def json_filters():
    filters = Filter.query.all()
    if not filters:
        flash(f"Error filter not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    filter = dict()
    for f in filters:
        filter[f.id] = f.filtername
    return jsonify(filter)


@app.route("/json/variant/<string:id>")
@app.route("/json/variant/<string:id>/version/<int:version>")
@app.route("/json/variant/<string:id>/family/<int:family>")
@app.route("/json/variant/<string:id>/family/<int:family>/version/<int:version>")
@login_required
def json_variant(id, version=-1, family=None):
    variant = Variant.query.get(id)

    samples = list()
    for v2s in variant.samples:
        same_family = False
        if v2s.sample.status >= 1:
            if family is not None and v2s.sample.family:
                if v2s.sample.familyid == family:
                    same_family = True
            allelic_frequency = v2s.allelic_depth / v2s.depth
            samples.append({
                "samplename": v2s.sample.samplename,
                "carrier": v2s.sample.carrier,
                "family": v2s.sample.family.family if v2s.sample.family else "",
                "same_family": same_family,
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


################################################################################


################################################################################
# Toggle boolean variables in DB

@app.route("/toggle/samples/variant/status", methods=['POST'])
@login_required
def toggle_varStatus():
    id_var = request.form["id_var"]
    sample_id = request.form["sample_id"]
    type = request.form["type"]
    v2s = Var2Sample.query.get((id_var, sample_id))
    if type == "analyse1":
        v2s.analyse1 = False if v2s.analyse1 else True
        return_value = v2s.analyse1
    if type == "analyse2":
        v2s.analyse2 = False if v2s.analyse2 else True
        return_value = v2s.analyse2
    if type == "reported":
        v2s.reported = False if v2s.reported else True
        return_value = v2s.reported
    db.session.commit()
    return f"{return_value}"


@app.route("/toggle/samples/variant/class", methods=['POST'])
@login_required
def toggle_varClass():
    id_var = request.form["id_var"]
    class_variant = request.form["class_variant"]
    variant = Variant.query.get(id_var)
    variant.class_variant = class_variant
    db.session.commit()
    return f"{variant.class_variant}"


@app.route("/toggle/sample/status", methods=['POST'])
@login_required
def toggle_sampleStatus():
    sample_id = request.form["sample_id"]
    sample = Sample.query.get(sample_id)

    if "status" in request.form:
        sample.status = request.form["status"]
        db.session.commit()
        return f"{sample} - {sample.status}"

    if sample.status == 1:
        sample.status = 2
        db.session.commit()
    return f"{sample} - {sample.status}"


@app.route("/add/comment/variant", methods=['POST'])
@login_required
def add_comment():
    comment = Comment(comment=urllib.parse.unquote(request.form["comment"]), variantid=request.form["id_var"], date=datetime.now(), userid=current_user.id)
    db.session.add(comment)
    db.session.commit()
    return 'ok'


@app.route("/add/filter", methods=['POST'])
@login_required
def add_filter():
    filter = Filter(
        filtername=urllib.parse.unquote(request.form["name"]),
        filter=json.loads(request.form["filter"])
    )
    db.session.add(filter)
    db.session.commit()
    return 'ok'


@app.route("/add/preferred", methods=['POST'])
@login_required
def add_preferred():
    user = db.session.query(User).filter_by(id=current_user.get_id()).first()
    print(user)
    print(user.transcripts)
    transcript = urllib.parse.unquote(request.form["transcript"])
    # transcript = Transcript.query.get(transcript_id)
    if transcript in user.transcripts:
        user.transcripts.remove(transcript)
    else:
        user.transcripts.append(transcript)
    print(user.transcripts)
    db.session.commit()
    print(user.transcripts)
    return 'ok'


################################################################################
