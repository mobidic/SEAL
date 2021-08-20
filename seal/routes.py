import os
import secrets
import json
import itertools
import re
import numpy
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, jsonify
from seal import app, db, bcrypt
from seal.forms import LoginForm, UpdateAccountForm, UpdatePasswordForm, UploadVariantForm, SelectFilterForm
from seal.models import User, Sample, Filter, Transcript, Family
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime

################################################################################
# Essentials pages


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


@app.route("/transcripts", methods=['GET', 'POST'])
@login_required
def transcripts():
    return render_template('analysis/transcripts.html', title='Transcripts',)


@app.route("/sample/<int:id>", methods=['GET', 'POST'])
@login_required
def sample(id):
    sample = db.session.query(Sample.samplename, Sample.id).filter(Sample.id==id).first()
    if not sample:
        flash(f"Error sample not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    filters = Filter.query.all()

    return render_template(
        'analysis/sample.html', title=f'{sample.samplename}',
        sample=sample,
        filters=filters
    )


def add_vcf(info, vcf_file):
    random_hex = secrets.token_hex(8)

    _, f_ext = os.path.splitext(vcf_file.filename)

    vcf_fn = random_hex + f_ext
    vcf_path = os.path.join(app.root_path, 'static/temp/vcf/', vcf_fn)
    vcf_file.save(vcf_path)

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
        sample = Sample.query.filter_by(samplename=uploadSampleForm.samplename.data).first()
        if sample:
            flash("This Sample Name is already in database!", "error")
            return redirect(url_for('index'))

        info = {
            "samplename": uploadSampleForm.samplename.data,
            "family": uploadSampleForm.family.data
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


@app.route("/json/samples", methods=['GET', 'POST'])
@login_required
def json_samples():
    samples = db.session.query(Sample.id, Sample.samplename, Sample.status, Sample.familyid).all()
    samples_json = {"data": list()}
    for sample in samples:
        family = None
        if sample.familyid is not None:
            family = Family.query.get(sample.familyid)
        samples_json["data"].append({
            "id": sample.id,
            "samplename": sample.samplename,
            "family": family.family if family else None,
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
    total_samples = db.session.query(Sample).count()

    # Get all canonical trancripts
    transcripts = db.session.query(Transcript.refSeq).filter_by(canonical=True).all()
    transcripts = list(itertools.chain(*transcripts))
    transcripts = [each.split('.')[0] for each in transcripts]

    ##################################################
    # Define some dict/array for calculation
    consequences_dict = {
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
    gnomADg = [
        "gnomADg_AF_AFR",
        "gnomADg_AF_AMR",
        "gnomADg_AF_ASJ",
        "gnomADg_AF_EAS",
        "gnomADg_AF_FIN",
        "gnomADg_AF_NFE",
        "gnomADg_AF_OTH"
    ]
    annot_to_split = [
        "Existing_variation",
        "Consequence",
        "CLIN_SIG",
        "SOMATIC",
        "PHENO",
        "PUBMED"
    ]
    missenses = [
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
    spliceAI = [
        "AG",
        "AL",
        "DG",
        "DL"
    ]
    ##################################################

    for variant in sample.variants:
        annotations = variant.annotations[version]["ANN"]
        features = list(annotations.keys())
        feature = None
        consequence_score_max = 0
        for value in features:
            # Split annotations
            for splitAnn in annot_to_split:
                try:
                    annotations[value][splitAnn] = annotations[value][splitAnn].split("&")
                except AttributeError:
                    annotations[value][splitAnn] = []

            # Get consequence score
            consequence_score = 0
            for consequence in annotations[value]["Consequence"]:
                consequence_score += consequences_dict[consequence]

            # Calcul position into the gene (Exons or Intron)
            if annotations[value]["EXON"] is not None:
                pos = annotations[value]["EXON"]
                annotations[value]["EI"] = f"Exon {pos}"
            elif annotations[value]["INTRON"] is not None:
                pos = annotations[value]["INTRON"]
                annotations[value]["EI"] = f"Intron {pos}"
            else:
                annotations[value]["EI"] = None

            # Calcul GnomAD AF for all population and get the max
            gnomadg_max = None
            gnomadg_max_pop = "ALL"
            for gnomADg_key in gnomADg:
                try:
                    annotations[value][gnomADg_key] = float(annotations[value][gnomADg_key])
                except ValueError:
                    annotations[value][gnomADg_key] = 0
                except TypeError:
                    annotations[value][gnomADg_key] = None

                if annotations[value][gnomADg_key] is not None:
                    if gnomadg_max is None or annotations[value][gnomADg_key] > gnomadg_max:
                        gnomadg_max = annotations[value][gnomADg_key]
                        gnomadg_max_pop = gnomADg_key
            annotations[value]["GnomADg_max"] = gnomadg_max
            annotations[value]["GnomADg_max_pop"] = gnomadg_max_pop

            # Get the canonical transcript with max consequences or
            # random NM or another one...
            annotations[value]["canonical"] = False
            if value in transcripts:
                if consequence_score_max <= consequence_score:
                    feature = value
                    annotations[feature]["canonical"] = True
                    consequence_score_max = consequence_score
            elif re.search("NM_", value) and not annotations[feature]["canonical"]:
                feature = value
            elif feature is None:
                feature = value

            # Calcul missenses scores
            missenseScores = list()
            for missense in missenses:
                if annotations[feature][missense] is not None:
                    missenseScores.append(float(annotations[feature][missense]))
            mean = numpy.mean(missenseScores)
            if numpy.isnan(mean):
                annotations[feature]["missenseMean"] = None
            else:
                annotations[feature]["missenseMean"] = mean

            # Get Max spliceAI
            maxSpliceAI_DS = None
            maxSpliceAI_DP = None
            maxSpliceAI_type = None
            for type in spliceAI:
                key_DS = f"SpliceAI_pred_DS_{type}"
                key_DP = f"SpliceAI_pred_DP_{type}"
                score = annotations[feature][key_DS]
                pos = annotations[feature][key_DP]
                if score is None:
                    continue
                if maxSpliceAI_DS is None or score > maxSpliceAI_DS:
                    maxSpliceAI_DS = score
                    maxSpliceAI_DP = pos
                    maxSpliceAI_type = type

            annotations[feature]["maxSpliceAI_DS"] = maxSpliceAI_DS
            annotations[feature]["maxSpliceAI_DP"] = maxSpliceAI_DP
            annotations[feature]["maxSpliceAI_type"] = maxSpliceAI_type

        occurrences = len(variant.samples)
        occurences_family = 0
        members = []
        for sam in variant.samples:
            if sam.familyid is not None and sam.familyid == sample.familyid and sam.id != sample.id:
                occurences_family += 1
                members.append(sam.samplename)

        variants["data"].append({
            "annotations": annotations[feature],
            "chr": f"{variant.chr}",
            "pos": f"{variant.pos}",
            "ref": f"{variant.ref}",
            "alt": f"{variant.alt}",
            "inseal": {
                "occurrences": occurrences,
                "total_samples": total_samples,
                "occurences_family": occurences_family,
                "members": members
            }
        })

    return jsonify(variants)


@app.route("/json/transcripts")
@login_required
def json_transcripts():
    transcripts = db.session.query(Transcript).all()
    transcripts_json = {"data": list()}
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


@app.route("/json/filter/<int:id>")
@login_required
def json_filter(id=1):
    filter = Filter.query.get(int(id))
    if not filter:
        flash(f"Error filter not found! Please contact your administrator! (id - {id})", category="error")
        return redirect(url_for('index'))

    return jsonify(filter.filter)


################################################################################
