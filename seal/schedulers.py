import os
import json
import datetime
from seal import app, scheduler, db
from seal.models import Sample, Variant, Family, Var2Sample
from anacore import annotVcf
import shlex
import subprocess


# cron examples
@scheduler.task('cron', id='import vcf', second="*/20")
def importvcf():
    files = os.listdir(os.path.join(app.root_path, 'static/temp/vcf/'))
    vep_config_file = os.path.join(app.root_path, 'static/vep.config.json')
    with open(vep_config_file, "r") as tf:
        vep_config = json.load(tf)

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
        vcf_vep = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.vep.vcf')
        stats_vep = os.path.join(app.root_path, 'static/temp/vcf/', f'{f_base}.vep.html')
        vep_cmd = "vep " + \
            f" --input_file {vcf_fn} " + \
            f" --output_file {vcf_vep} " + \
            f" --stats_file {stats_vep} " + \
            f" --dir {vep_config['dir']} " + \
            f" --plugin dbNSFP,{vep_config['dbNSFP']},BayesDel_addAF_rankscore,BayesDel_noAF_rankscore,CADD_raw_rankscore,CADD_raw_rankscore_hg19,ClinPred_rankscore,DANN_rankscore,DEOGEN2_rankscore,Eigen-PC-raw_coding_rankscore,Eigen-raw_coding_rankscore,FATHMM_converted_rankscore,GERP++_RS_rankscore,GM12878_fitCons_rankscore,GenoCanyon_rankscore,H1-hESC_fitCons_rankscore,HUVEC_fitCons_rankscore,LINSIGHT_rankscore,LIST-S2_rankscore,LRT_converted_rankscore,M-CAP_rankscore,MPC_rankscore,MVP_rankscore,MetaLR_rankscore,MetaSVM_rankscore,MutPred_rankscore,MutationAssessor_rankscore,MutationTaster_converted_rankscore,PROVEAN_converted_rankscore,Polyphen2_HDIV_rankscore,Polyphen2_HVAR_rankscore,PrimateAI_rankscore,REVEL_rankscore,SIFT4G_converted_rankscore,SIFT_converted_rankscore,SiPhy_29way_logOdds_rankscore,VEST4_rankscore,bStatistic_converted_rankscore,fathmm-MKL_coding_rankscore,fathmm-XF_coding_rankscore,integrated_fitCons_rankscore,phastCons100way_vertebrate_rankscore,phastCons17way_primate_rankscore,phastCons30way_mammalian_rankscore,phyloP100way_vertebrate_rankscore,phyloP17way_primate_rankscore,phyloP30way_mammalian_rankscore " + \
            f" --plugin  MaxEntScan,{vep_config['MaxEntScan']} " + \
            f" --plugin SpliceAI,snv={vep_config['SpliceAI_snv']},indel={vep_config['SpliceAI_indel']} " + \
            f" --plugin dbscSNV,{vep_config['dbscSNV']} " + \
            f" --custom {vep_config['gnomADg']},gnomADg,vcf,exact,0,AF_AFR,AF_AMR,AF_ASJ,AF_EAS,AF_FIN,AF_NFE,AF_OTH " + \
            f" --fasta {vep_config['fasta']} " + \
            f" --fork {vep_config['fork']} " + \
            " --species homo_sapiens " + \
            " --assembly GRCh37 " + \
            " --cache " + \
            " --offline " + \
            " --merged " + \
            " --buffer_size 5000 " + \
            " --vcf " + \
            " --variant_class " + \
            " --sift b " + \
            " --polyphen b " + \
            " --nearest transcript " + \
            " --distance 5000,5000 " + \
            " --overlaps " + \
            " --gene_phenotype " + \
            " --regulatory " + \
            " --show_ref_allele " + \
            " --total_length " + \
            " --numbers " + \
            " --vcf_info_field ANN " + \
            " --terms SO " + \
            " --shift_3prime 1 " + \
            " --shift_genomic 1 " + \
            " --hgvs " + \
            " --hgvsg " + \
            " --shift_hgvs 1 " + \
            " --transcript_version " + \
            " --protein " + \
            " --symbol " + \
            " --ccds " + \
            " --uniprot " + \
            " --tsl " + \
            " --appris " + \
            " --canonical " + \
            " --biotype " + \
            " --domains " + \
            " --xref_refseq " + \
            " --check_existing " + \
            " --clin_sig_allele 1 " + \
            " --pubmed " + \
            " --var_synonyms " + \
            " --force"

        app.logger.info("------ Variant Annotation with VEP ------")
        args_vep = shlex.split(vep_cmd)
        app.logger.info(args_vep)
        with subprocess.Popen(args_vep, stdout=subprocess.PIPE) as proc:
            app.logger.info(f"------ {proc.stdout.read()}")
        app.logger.info("------ END VEP ------")

        try:
            with annotVcf.AnnotVCFIO(vcf_vep) as vcf_io:
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
            os.remove(vcf_vep)
            os.remove(stats_vep)
        finally:
            db.session.commit()
            app.logger.info(f"---- Variant for Sample Added : {sample} - {sample.id} ----")
            os.remove(os.path.join(app.root_path, 'static/temp/vcf/.lock'))
