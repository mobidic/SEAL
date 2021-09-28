import os
import json
import datetime
from seal import app, scheduler, db
from seal.models import Sample, Variant, Family, Var2Sample
from anacore import annotVcf


# cron examples
@scheduler.task('cron', id='import vcf', second="*/20")
def importvcf():
    files = os.listdir(os.path.join(app.root_path, 'static/temp/vcf/'))
    curr_token = False
    for f in files:
        if f.endswith(".token"):
            curr_token = f
            continue

    if curr_token and not os.path.exists(os.path.join(app.root_path, 'static/temp/vcf/.lock')):
        # Create lock file
        lockFile = open(os.path.join(app.root_path, 'static/temp/vcf/.lock'), 'x')
        lockFile.close()

        f_base, f_ext = os.path.splitext(curr_token)
        old_fn = os.path.join(app.root_path, 'static/temp/vcf/', curr_token)
        current_fn = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.treat')
        os.rename(old_fn, current_fn)
        with open(current_fn, "r") as tf:
            data = json.load(tf)
            samplename = data['samplename']

            # Add family in database if necessary
            familyid = None
            if "family" in data and data["family"] != "":
                familyname = data['family']
                family = Family.query.filter_by(family=familyname).first()
                if not family:
                    family = Family(family=familyname)
                    db.session.add(family)
                    db.session.commit()
                familyid = family.id

            carrier = False
            if "carrier" in data and data["carrier"] != "":
                carrier = data['carrier']
            index = False
            if "index" in data and data["index"] != "":
                index = data['index']

            sample = Sample(samplename=samplename, familyid=familyid, carrier=carrier, index=index)
            db.session.add(sample)
            db.session.commit()
            app.logger.info(f"---- Sample Added : {sample} - {sample.id} ----")

        current_date = datetime.datetime.now().isoformat()

        vcf_fn = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.vcf')

        try:
            with annotVcf.AnnotVCFIO(vcf_fn) as vcf_io:
                for v in vcf_io:
                    if v.alt[0] == "*":
                        continue
                    variant = Variant.query.get(f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}")
                    if not variant:
                        annotations = [{
                            "date": current_date,
                            "ANN": dict()
                        }]

                        for annot in v.info["ANN"]:
                            try:
                                wout_version = annot["Feature"].split('.')[0]
                            except AttributeError:
                                wout_version = "intergenic"
                            annotations[-1]["ANN"][wout_version] = annot
                        # app.logger.debug(f"       - Create Variant : {sample}")
                        variant = Variant(id=f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}", chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0], annotations=annotations)
                        db.session.add(variant)

                    # sample.variants.append(variant)
                    v2s = Var2Sample(variant_ID=variant.id, sample_ID=sample.id, depth=v.getPopDP(), allelic_depth=v.getPopAltAD()[0])
                    db.session.add(v2s)

        except Exception as e:
            db.session.remove()
            app.logger.info(f"{type(e).__name__} : {e}")
            sample = Sample.query.get(sample.id)
            sample.status = -1
        else:
            sample.status = 1
            os.remove(current_fn)
            os.remove(vcf_fn)
        finally:
            db.session.commit()
            app.logger.info(f"---- Variant for Sample Added : {sample} - {sample.id} ----")
            os.remove(os.path.join(app.root_path, 'static/temp/vcf/.lock'))
