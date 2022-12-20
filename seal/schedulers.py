import re
import json
import numpy
import shlex
import random
import datetime
import subprocess

from pathlib import Path
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_

from anacore import annotVcf

from seal import app, scheduler, db
from seal.models import Sample, Variant, Family, Var2Sample, Run, Transcript, Team, Bed


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


def get_token(path_tokens):
    for file in path_tokens.iterdir():
        if file.suffix == '.token':
            return file
    return False


def random_color(format="HEX"):
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)
    if format == "HEX":
        return f'#{red:02X}{green:02X}{blue:02X}'
    if format == "RGB":
        return f'rgb({red},{green},{blue})'
    if format == "RGBA":
        alpha = random.random.uniform(0, 1)
        return f'rgba({red},{green},{blue},{alpha})'


def is_valid_color(color):
    # Inspired by : https://regexr.com/39cgj & https://regex101.com/r/sY0nN9/1
    match_hex = bool(re.search(r'^(\#(([a-fA-F0-9]){3}){1,2})$', str(color), re.IGNORECASE))
    match_rgb = bool(re.search(r'^((rgb)?\s*?\(\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?,\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?,\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?\))$', str(color), re.IGNORECASE))
    match_rgba = bool(re.search(r'^((rgba)?\s*?\(\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?,\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?,\s*?(000|0?\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\s*?,\s*?(0|0\.\d*|1|1.0*)\s*?\))$', str(color), re.IGNORECASE))
    print(match_hex)
    print(match_rgb)
    print(match_rgba)
    return bool(match_hex | match_rgb | match_rgba)


def get_family(id=None, name=None):
    if id:
        family = Family.query.get(id)
        if family:
            return family
    if name:
        family = Family.query.filter_by(family=name).first()
        if bool(family):
            return family
        else:
            family = Family(family=name)
            db.session.add(family)
            db.session.commit()
            app.logger.info(f'{family} added to SEAL !')
            return family
    return False


def get_run(id=None, name=None, alias=None):
    if id:
        run = Run.query.get(id)
        if run:
            return run
    if name:
        run = Run.query.filter_by(name=name).first()
        if bool(run):
            if run.alias is None and alias:
                run.alias = alias
                db.session.commit()
            return run
        else:
            run = Run(name=name, alias=alias)
            db.session.add(run)
            db.session.commit()
            app.logger.info(f'{run} added to SEAL !')
            return run
    return False


def get_team(id=None, name=None, color=None):
    if id:
        team = Team.query.get(id)
        if team:
            return team
    if name:
        team = Team.query.filter_by(teamname=name).first()
        if bool(team):
            return team
        else:
            color = color if is_valid_color(color) else random_color()
            team = Team(teamname=name, color=color)
            db.session.add(team)
            db.session.commit()
            app.logger.info(f'{team} added to SEAL !')
            return team
    return False


def get_bed(id=None, name=None):
    if id:
        bed = Bed.query.get(id)
        if bed:
            return bed
    if name:
        bed = Bed.query.filter_by(name=name).first()
        if bool(bed):
            return bed
    return False


def create_sample(data):
    if not "samplename" in data:
        raise KeyError

    samplename = data["samplename"]
    sample = Sample(samplename=samplename)

    if "affected" in data:
        sample.affected = bool(data["affected"])
    if "index" in data:
        sample.index = bool(data["index"])

    if "family" in data:
        id = data["family"]["id"] if "id" in data["family"] else None
        name = data["family"]["name"] if "name" in data["family"] else None
        family = get_family(id, name)
        if family:
            sample.family = family

    if "run" in data:
        id = data["run"]["id"] if "id" in data["run"] else None
        name = data["run"]["name"] if "name" in data["run"] else None
        alias = data["run"]["alias"] if "alias" in data["run"] else None
        run = get_run(id, name, alias)
        if run:
            sample.run = run

    if "teams" in data:
        teams = data["teams"]
        for t in teams:
            id = t["id"] if "id" in t else None
            name = t["name"] if "name" in t else None
            color = t["color"] if "color" in t else None
            team = get_team(id, name, color)
            if team:
                sample.teams.append(team)

    if "bed" in data:
        id = data["bed"]["id"] if "id" in data["bed"] else None
        name = data["bed"]["name"] if "name" in data["bed"] else None
        bed = get_bed(id, name)
        if bed:
            sample.bed = bed

    db.session.commit()
    return sample


class CommandFailedError(Exception):
    def __init__(self, returncode, stderr):
        self.returncode = returncode
        self.stderr = stderr

    def __str__(self):
        return f"Command failed with exit code {self.returncode} and error output: {self.stderr}"


def extract_command_and_args(data, values):
    """
    Extract the command and arguments from the JSON data and format them using the provided values.

    Args:
        data (dict): A dictionary containing the command and arguments. The command should be stored in the 'command' key,
                     and the arguments should be stored in the 'args' key as a dictionary.
        values (dict): A dictionary of values to be used to replace placeholders in the command arguments.

    Returns:
        tuple: A tuple containing the command and a list of formatted arguments.
    """
    # Extract the command and arguments from the data dictionary
    command = data['command']
    args = data['args']

    # Initialize an empty list to store the formatted arguments
    formatted_args = []

    # Iterate over the items in the args dictionary
    for key, value in args.items():
        # If the value is a boolean and is True, add the key to the formatted arguments list
        if isinstance(value, bool):
            if value:
                formatted_args.append(key)
        # If the value is a string, int, or float, format it using the values dictionary and add the key and formatted value to the formatted arguments list
        elif isinstance(value, (str, int, float)):
            formatted_args.append(key)
            f_string = f"{value}"
            formatted_value = f_string.format_map(values)
            formatted_args.append(formatted_value)
        # If the value is a list, iterate over the items in the list and process them in the same way as a string, int, or float value
        elif isinstance(value, list):
            for sub_value in value:
                formatted_args.extend([key, f"{sub_value}".format_map(values)])

    # Return a tuple containing the command and the formatted arguments list
    return command, formatted_args


def execute_shell_command(shell_command):
    """Execute a shell command and log the standard output and error streams.

    Args:
        shell_command (list): A list containing the command and its arguments.

    Returns:
        tuple: A tuple containing the exit code and output of the command.
    """
    try:
        output = subprocess.run(shell_command, capture_output=True, check=True)
        app.logger.info(f"Command {shell_command} executed successfully with output: {output.stdout}")
        return (output.returncode, output.stdout)
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Command {shell_command} failed with exit code {e.returncode} and error output: {e.stderr}")
        raise CommandFailedError(e.returncode, e.stderr)


def create_and_execute_shell_command(json_file, values):
    """Create and execute a shell command from a JSON file.

    Args:
        json_file (str): The path to the JSON file containing the command and its arguments.
        values (dict): A dictionary of values to be used to replace placeholders in the command arguments.

    Returns:
        tuple: A tuple containing the exit code and output of the command.
    """
    # Load the JSON data from the file
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Extract the command and arguments from the JSON data
    command, args = extract_command_and_args(data, values)

    # Create the shell command by concatenating the command and arguments
    shell_command = [command] + args

    # Execute the shell command
    exit_code, output = execute_shell_command(shell_command)

    # If the exit code is non-zero, raise a custom exception
    if exit_code != 0:
        raise CommandFailedError(exit_code, output)

    # Return the exit code and output
    return exit_code, output


# cron examples
@scheduler.task('cron', id='import vcf', second="*/20")
def importvcf():
    # Load config file

    # Check launchable
    path_inout = Path(app.root_path).joinpath('static/temp/vcf/')
    current_token = get_token(path_inout)
    path_locker = path_inout.joinpath('.lock')

    if current_token and not path_locker.exists():
        app.logger.info("---------------- Create A New Sample ----------------")

        # Create lock file
        lockFile = open(path_locker, 'x')
        lockFile.close()

        # Change token to treat file
        current_file = current_token.with_suffix('.treat')
        current_token.rename(current_file)

        # Load data
        with current_file.open('r') as json_sample:
            data = json.load(json_sample)

        # Come from interface
        try:
            interface = data["interface"]
        except KeyError:
            interface = False
        
        vcf_path = Path(data["vcf_path"])
        if not vcf_path.exists():
            app.logger.error(f'Path does not exist for : {vcf_path}')
            return

        sample = create_sample(data)
        current_date = datetime.datetime.now().isoformat()

        vcf_vep = path_inout.joinpath(f'{vcf_path.stem}.vep.vcf')
        stats_vep = path_inout.joinpath(f'{vcf_path.stem}.vep.html')

        values = {
            "vcf_path": vcf_path,
            "vcf_vep": vcf_vep,
            "stats_vep": stats_vep
        }

        try:
            app.logger.info("------ Variant Annotation with VEP ------")
            create_and_execute_shell_command(Path(app.root_path).joinpath('static/vep.config.json'), values)
            app.logger.info("------ END VEP ------")
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
                                if splitAnn == 'VAR_SYNONYMS':
                                    try:
                                        var_synonyms = dict()
                                        for vs in annot[splitAnn].split("--"):
                                            key, values = vs.split("::")
                                            values_array = values.split("&")
                                            var_synonyms[key] = values_array

                                        annot[splitAnn] = var_synonyms
                                    except AttributeError:
                                        annot[splitAnn] = dict()
                                else:
                                    try:
                                        annot[splitAnn] = annot[splitAnn].split("&")
                                    except AttributeError:
                                        annot[splitAnn] = []

                            # transcript
                            transcript = Transcript.query.get(annot["Feature"])
                            if not transcript and annot["Feature"] is not None:
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

        except CommandFailedError as e:
            app.logger.info(f"{type(e).__name__} : {e}")
            sample.status = -1
        except Exception as e:
            db.session.remove()
            app.logger.info(f"{type(e).__name__} : {e}")
            sample = Sample.query.get(sample.id)
            sample.status = -1
        else:
            sample.status = 1
            current_file.unlink()
            if interface:
                vcf_path.unlink()
            vcf_vep.unlink()
            stats_vep.unlink()
        finally:
            db.session.commit()
            app.logger.info(f"---- Variant for Sample Added : {sample} - {sample.id} ----")
            path_locker.unlink()
