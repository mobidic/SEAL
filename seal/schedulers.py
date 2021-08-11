import os
import json
import datetime
from seal import app, scheduler, db
from seal.models import Sample, Variant
from anacore import annotVcf


def splitAnnot(annot, char="&"):
    try:
        return annot.split(char)
    except AttributeError:
        return ["NA"]


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

        current_date = datetime.datetime.now().isoformat()
        annot_to_split = [
            "Existing_variation",
            "Consequence",
            "CLIN_SIG",
            "SOMATIC",
            "PHENO",
            "PUBMED"
        ]
        gnomADg = [
            "gnomADg_AF_AFR",
            "gnomADg_AF_AMR",
            "gnomADg_AF_ASJ",
            "gnomADg_AF_EAS",
            "gnomADg_AF_FIN",
            "gnomADg_AF_NFE",
            "gnomADg_AF_OTH"
        ]
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
                            for splitAnn in annot_to_split:
                                annot[splitAnn] = splitAnnot(annot[splitAnn])

                            gnomadg_max = None
                            gnomadg_max_pop = "ALL"
                            for gnomADg_key in gnomADg:
                                try:
                                    annot[gnomADg_key] = float(annot[gnomADg_key])
                                except ValueError:
                                    annot[gnomADg_key] = 0
                                except TypeError:
                                    annot[gnomADg_key] = None

                                if annot[gnomADg_key] is not None:
                                    if gnomadg_max is None or annot[gnomADg_key] > gnomadg_max:
                                        gnomadg_max = annot[gnomADg_key]
                                        gnomadg_max_pop = gnomADg_key
                            annot["GnomADg_max"] = gnomadg_max
                            annot["GnomADg_max_pop"] = gnomadg_max_pop

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
