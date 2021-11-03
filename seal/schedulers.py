import os
import json
import numpy
import datetime
from seal import app, scheduler, db
from seal.models import Sample, Variant, Family, Var2Sample, Run, Transcript
from anacore import annotVcf
import shlex
import subprocess


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
    "PUBMED",
    "TRANSCRIPTION_FACTORS",
    "VAR_SYNONYMS",
    "DOMAINS",
    "FLAGS"
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
    "SpliceAI_pred_DS_AG",
    "SpliceAI_pred_DS_AL",
    "SpliceAI_pred_DS_DG",
    "SpliceAI_pred_DS_DL"
]


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
            vcf_path = data['vcf_path']
            interface = False
            if "interface" in data and data["interface"] is True:
                interface = True

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

            # Add run in database if necessary
            runid = None
            if "run" in data and data["run"] != "":
                run_name = data['run']
                run = Run.query.filter_by(run_name=run_name).first()
                if not run:
                    run = Run(run_name=run_name)
                    db.session.add(run)
                    db.session.commit()
                runid = run.id
            app.logger.info(f"---- {runid} ----")

            carrier = False
            if "carrier" in data and data["carrier"] != "":
                carrier = data['carrier']
            index = False
            if "index" in data and data["index"] != "":
                index = data['index']

            sample = Sample(samplename=samplename, familyid=familyid, runid=runid, carrier=carrier, index=index)
            db.session.add(sample)
            db.session.commit()
            app.logger.info(f"---- Sample Added : {sample} - {sample.id} ----")

        current_date = datetime.datetime.now().isoformat()

        vcf_fn = os.path.join(vcf_path)
        baseout = os.path.basename(os.path.splitext(vcf_path)[0])
        vcf_vep = os.path.join(app.root_path, "static/temp/vcf/", f"{baseout}.vep.vcf")
        stats_vep = os.path.join(app.root_path, "static/temp/vcf/", f"{baseout}.vep.html")
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
                            "ANN": list()
                        }]

                        for annot in v.info["ANN"]:
                            # Split annotations
                            for splitAnn in ANNOT_TO_SPLIT:
                                try:
                                    annot[splitAnn] = annot[splitAnn].split("&")
                                except AttributeError:
                                    annot[splitAnn] = []

                            # transcript
                            transcript = Transcript.query.get(annot["Feature"])
                            if not transcript:
                                transcript = Transcript(
                                    feature=annot["Feature"],
                                    biotype=annot["BIOTYPE"],
                                    feature_type=annot["Feature_type"],
                                    symbol=annot["SYMBOL"],
                                    symbol_source=annot["SYMBOL_SOURCE"],
                                    gene=annot["Gene"],
                                    source=annot["SOURCE"],
                                    protein=annot["ENSP"],
                                    canonical=annot["CANONICAL"],
                                    hgnc=annot["HGNC_ID"]
                                )
                                db.session.add(transcript)

                            # Get consequence score
                            consequence_score = 0
                            for consequence in annot["Consequence"]:
                                consequence_score += CONSEQUENCES_DICT[consequence]
                            annot["consequenceScore"] = consequence_score

                            # Get Exon/Intron
                            annot["EI"] = None
                            if annot["EXON"] is not None:
                                annot["EI"] = f"Exon {annot['EXON']}"
                            if annot["INTRON"] is not None:
                                annot["EI"] = f"Intron {annot['INTRON']}"

                            # Get Exon/Intron
                            annot["canonical"] = True if annot['CANONICAL'] == 'YES' else False

                            # missense
                            missenses = list()
                            for value in MISSENSES:
                                missenses.append(annot[value])
                            missenses = numpy.array(missenses, dtype=numpy.float64)
                            mean = numpy.nanmean(missenses)
                            annot["missensesMean"] = None if numpy.isnan(mean) else mean

                            # max gnomad
                            gnomad = list()
                            for value in GNOMADG:
                                gno = None if annot[value] == "." else annot[value]
                                gnomad.append(gno)
                            gnomad = numpy.array(gnomad, dtype=numpy.float64)
                            max = numpy.nanmax(gnomad)
                            annot["gnomadMax"] = None if numpy.isnan(max) else max

                            # max spliceAI
                            spliceAI = list()
                            for value in SPLICEAI:
                                spliceAI.append(annot[value])
                            spliceAI = numpy.array(spliceAI, dtype=numpy.float64)
                            max = numpy.nanmax(spliceAI)
                            annot["spliceAI"] = None if numpy.isnan(max) else max

                            # max MaxEntScan
                            annot["MES_var"] = None
                            if annot["MaxEntScan_alt"] is not None and annot["MaxEntScan_ref"] is not None:
                                annot["MES_var"] = -100 + (float(annot["MaxEntScan_alt"]) * 100) / float(annot["MaxEntScan_ref"])

                            annotations[-1]["ANN"].append(annot)

                        # app.logger.debug(f"       - Create Variant : {sample}")
                        variant = Variant(id=f"{v.chrom}-{v.pos}-{v.ref}-{v.alt[0]}", chr=v.chrom, pos=v.pos, ref=v.ref, alt=v.alt[0], annotations=annotations)
                        db.session.add(variant)

                    # sample.variants.append(variant)
                    v2s = Var2Sample(variant_ID=variant.id, sample_ID=sample.id, depth=v.getPopDP(), allelic_depth=v.getPopAltAD()[0], filter=v.filter)
                    db.session.add(v2s)

        except Exception as e:
            db.session.remove()
            app.logger.info(f"{type(e).__name__} : {e}")
            sample = Sample.query.get(sample.id)
            sample.status = -1
        else:
            sample.status = 1
            os.remove(current_fn)
            if interface:
                os.remove(vcf_fn)
            os.remove(vcf_vep)
            os.remove(stats_vep)
        finally:
            db.session.commit()
            app.logger.info(f"---- Variant for Sample Added : {sample} - {sample.id} ----")
            os.remove(os.path.join(app.root_path, 'static/temp/vcf/.lock'))
