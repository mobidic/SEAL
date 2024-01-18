# (c) 2023, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2023  Jean-Charles DELMAS - MoBiDiC - CHU Montpellier
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
from pathlib import Path
import json
import os
import sys
import shutil
import tempfile
import pandas as pd
import re
import logging

# Function to load and validate the CSV file
def load_and_validate_csv(csv_path, sep=","):
    df = pd.read_csv(csv_path, sep=sep)

    # Check for required headers (without asterisks)
    required_headers = ["Sample Name", "Run ID", "Run Alias", "Panel"]
    for header in required_headers:
        if header not in df.columns or df[header].isnull().any():
            raise ValueError(f"The column '{header}' is required and must not contain null values.")
    return df

def determine_file_type(row):
    if 'MOC' in row['Panel']:
        return 'MOC'
    elif 'KAB' in row['Panel']:
        return 'KAB'
    elif 'MAI' in row['Panel']:
        return 'MAI'
    return 'Unknown'

def generate_all_samples_txt(df, output_filename, base_path="/"):
    with open(output_filename, 'w') as file:
        for _, row in df.iterrows():
            file_type = determine_file_type(row)

            if file_type == 'MOC':
                run_alias = re.sub(r'([a-zA-Z]{3})(\d+)', r'\1-\2', row['Run Alias'])
                vcf_path = f"{base_path}/NGS/MOC/ACHAB-MOC/{run_alias}/{row['Sample Name']}/panelCapture/{row['Sample Name']}.vcf"

            elif file_type == 'KAB':
                run_alias = re.sub(r'([a-zA-Z]{3})(\d+)', r'\1-\2', row['Run Alias'])
                vcf_path = f"{base_path}/NGS/KAB/ACHAB-a-partir_KAB42/{run_alias}/{row['Sample Name']}/panelCapture/{row['Sample Name']}.vcf"

            elif file_type == 'MAI':
                # Extract the numeric part of the 'Run Alias' (e.g., '151' from 'MAI151')
                run_alias_num = int(re.search(r'MAI(\d+)', row['Run Alias']).group(1))

                # Determine the correct panel folder based on the alias number range
                panel_folder = ""
                if 89 <= run_alias_num <= 112:
                    panel_folder = "Panel_302genes"
                elif 113 <= run_alias_num <= 126:
                    panel_folder = "Panel_302genes_v2"
                elif 127 <= run_alias_num <= 140:
                    panel_folder = "Panel_300genes"
                elif 141 <= run_alias_num <= 152:
                    panel_folder = "Panel_261genes"

                # Search for the specific folder containing 'MAI' and the number before '_captures'
                specific_folder = None
                for d in os.listdir(os.path.join(base_path, "NGS", "MAI", panel_folder)):
                    """
                    Check if the folder name contains the 'MAI' alias number before '_captures'.
                    For example, for MAI151, it checks for 'MAI-151' in 'MAI-151_152_captures_FT-153363'
                    """
                    if f"MAI-{run_alias_num}" in d.split('_captures')[0]:
                        specific_folder = d
                        break

                # Construct the VCF file path if a specific folder is found
                if specific_folder:
                    vcf_path = os.path.join(base_path, "NGS", "MAI", panel_folder, specific_folder, row['Sample Name'], "panelCapture", f"{row['Sample Name']}.vcf")
                else:
                    logging.error(f"Specific folder for MAI-{run_alias_num} not found in {panel_folder}")
                continue

            else:
                logging.warning(f"Unknown file type for row: {row}")
                continue

            if not Path(vcf_path).exists():
                logging.error(f"Path does not exist : {vcf_path}")
                continue

            data_entry = {
                'samplename': row['Sample Name'],
                'family': {
                    'name': row['Family']
                },
                'run': {
                    'name': row['Run ID'],
                    'alias': run_alias
                },
                'teams': [{"name":row['Team']}],
                'vcf_path': vcf_path
            }
            file.write(json.dumps(data_entry) + '\n')

    logging.debug(f"File {output_filename} generated successfully.")
    return output_filename

def create_treat_files(input_file, output_dir):
    if not input_file:
        logging.error("Error: No input file specified.")
        return [], ""

    temp_dir = tempfile.mkdtemp(dir=os.path.dirname(output_dir))
    treat_files = []
    replace_all = None

    with open(input_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        try:
            data = json.loads(line.strip())
            samplename = data['samplename']
            run_alias = data['run']['alias']

            if 'MAI' in run_alias or 'KAB' in run_alias:
                run_alias = re.sub(r'([a-zA-Z]{3})(\d+)', r'\1-\2', run_alias).strip()

            treat_filename = os.path.join(temp_dir, f"{samplename}-{run_alias}.treat")

            if os.path.exists(treat_filename) and replace_all is None:
                replace_choice = input(f"The file {treat_filename} already exists. Do you want to replace it? (yes/no/all)")
                if replace_choice.lower() == 'all':
                    replace_all = True
                elif replace_choice.lower() == 'no':
                    i = 1
                    while os.path.exists(f"{treat_filename}({i})"):
                        i += 1
                    treat_filename = f"{treat_filename}({i})"
                    replace_all = False

            with open(treat_filename, 'w') as treat_file:
                treat_file.write(json.dumps(data))
                treat_files.append(treat_filename)
                logging.info(f".treat file created or replaced: {treat_filename}")

        except json.JSONDecodeError:
            logging.error(f"JSON format error in the line: {line.strip()}")

    return treat_files, temp_dir

def main(args):
    csv_path = args.input
    output_dir = args.output
    args.separator
    
    logging.basicConfig(level=int(args.log_level)*10)
    try:
        dataframe = load_and_validate_csv(csv_path)
        txt_file = generate_all_samples_txt(dataframe, "all_samples.txt", args.base_path)
        treat_files, temp_dir = create_treat_files(txt_file, output_dir)

        if treat_files: 
            choice = input("Do you want to import the .treat files into SEAL? (yes/no)")
            if choice.lower() == 'yes':
                for treat_file in treat_files:
                    token_file = os.path.basename(treat_file).replace('.treat', '.token')
                    token_path = os.path.join(output_dir, token_file)
                    try:
                        shutil.move(treat_file, token_path)
                        logging.info(f"File imported into SEAL: {token_path}")
                    except FileNotFoundError:
                        logging.error(f"Error moving file: {treat_file}")
                shutil.rmtree(temp_dir)
            else:
                logging.info(f"The .treat files have been stored in: {temp_dir}")

    except ValueError as e:
        logging.error(e)

############____MAIN____############

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEAL db - Simple, Efficient And Lite database for NGS")
    parser.add_argument('-i', '--input', help='Input CSV', required=True)
    parser.add_argument('-o', '--output', help='Output', default=Path(os.getcwd()).joinpath("seal/static/temp/vcf"))
    parser.add_argument('-b', '--base-path', help='Base path', default="/")
    parser.add_argument('-s', '--separator', help='Separator', default=",")
    parser.add_argument('-l', '--log-level', help='Log level ([0-5])', default=0)
    args = parser.parse_args()

    main(args)
    logging.info("Operation completed.")
    sys.exit(0)