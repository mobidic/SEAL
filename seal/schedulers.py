import os
import json
from seal import app, scheduler, db
from seal.models import Sample, Variant
from anacore import annotVcf


# cron examples
@scheduler.task('cron', id='import vcf', second="*/10")
def importvcf():
    files = os.listdir(os.path.join(app.root_path, 'static/temp/vcf/'))
    for f in files:
        if f.endswith(".token"):
            f_base, f_ext = os.path.splitext(f)
            old_fn = os.path.join(app.root_path, 'static/temp/vcf/', f)
            current_fn = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.treat')
            os.rename(old_fn, current_fn)
            with open(current_fn, "r") as tf:
                data = json.load(tf)
                samplename = data['samplename']
                sample = Sample(samplename=samplename)
                app.logger.info(f"Add sample : {sample}")
                db.session.add(sample)
                db.session.commit()

            vcf_fn = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.vcf')
            with annotVcf.AnnotVCFIO(vcf_fn) as vcf_io:
                for v in vcf_io:
                    variant = Variant.query.filter_by(chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0]).first()
                    if not variant:
                        variant = Variant(chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0])
                        db.session.add(variant)
                        db.session.commit()

                    sample.variants.append(variant)

                db.session.commit()
            app.logger.info(f"End added sample : {sample}")
