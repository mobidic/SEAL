import os
import json
import datetime
from seal import app, scheduler, db
from seal.models import Sample, Variant, Family
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

    if curr_token:
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

            sample = Sample(samplename=samplename, familyid=familyid)
            app.logger.info(f"---- Add sample : {sample} ----")
            db.session.add(sample)
            db.session.commit()

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
                            wout_version = annot["Feature"].split('.')[0]
                            annotations[-1]["ANN"][wout_version] = annot
                        # app.logger.debug(f"       - Create Variant : {sample}")
                        variant = Variant(id=f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}", chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0], annotations=annotations)
                        db.session.add(variant)

                    sample.variants.append(variant)
        except Exception as e:
            print(e)
            sample.status = -1
        else:
            sample.status = 1
        finally:
            db.session.commit()
            app.logger.info(f"---- End added sample : {sample} ----")
