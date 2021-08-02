import os
import json
from seal import app, scheduler, db
from seal.models import Sample, Variant
from anacore import annotVcf


# cron examples
@scheduler.task('cron', id='import vcf', minute="*/1")
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
            sample = Sample(samplename=samplename)
            app.logger.info(f"---- Add sample : {sample} ----")
            db.session.add(sample)
            db.session.commit()

        vcf_fn = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.vcf')
        with annotVcf.AnnotVCFIO(vcf_fn) as vcf_io:
            for v in vcf_io:
                variant = Variant.query.get(f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}")
                if not variant:
                    # app.logger.debug(f"       - Create Variant : {sample}")
                    variant = Variant(id=f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}", chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0])
                    db.session.add(variant)

                sample.variants.append(variant)

        db.session.commit()

        app.logger.info(f"---- End added sample : {sample} ----")
