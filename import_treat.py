import json
import os
import sys
import shutil
import tempfile
import pandas as pd
import re

# File path for the CSV (manually update this)
csv_path = '/home/jcdelmas/Documents/SampleUMAI.csv'
output_dir = '/home/jcdelmas/Bureau/SEAL/seal/static/temp/vcf'

# Function to load and validate the CSV file
def load_and_validate_csv(csv_path):
    df = pd.read_csv(csv_path)

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

def determine_file_type(row):
    if 'MOC' in row['Panel']:
        return 'MOC'
    elif 'KAB' in row['Panel']:
        return 'KAB'
    elif 'MAI' in row['Panel']:
        return 'MAI'
    return 'Unknown'

def generate_test_txt(df, output_filename):
    with open(output_filename, 'w') as file:
        for _, row in df.iterrows():
            file_type = determine_file_type(row)

            if file_type == 'MOC':
                run_alias = re.sub(r'([a-zA-Z]{3})(\d+)', r'\1-\2', row['Run Alias'])
                vcf_path = f"/mnt/chu-ngs/Labos/UMAI/NGS/MOC/ACHAB-MOC/{run_alias}/*/panelCapture/{row['Sample Name']}.vcf"

            elif file_type == 'KAB':
                run_alias = row['Run Alias']
                vcf_path = f"/mnt/chu-ngs/Labos/UMAI/NGS/KAB/ACHAB-a-partir_KAB42/{run_alias}/*/panelCapture/{row['Sample Name']}.vcf"

            elif file_type == 'MAI':
                run_alias = row['Run Alias']
                vcf_path = f"/mnt/chu-ngs/Labos/UMAI/NGS/MAI/MobiDL/*//{row['Sample Name']}.vcf"

            else:
                print(f"Unknown file type for row: {row}")
                continue

            data_entry = {
                'samplename': row['Sample Name'],
                'run': {
                    'name': row['Run ID'],
                    'alias': run_alias
                },
                'vcf_path': vcf_path
            }
            file.write(json.dumps(data_entry) + '\n')

    print(f"File {output_filename} generated successfully.")
    return output_filename

# Function to create a .treat file with duplicate handling
def create_treat_files(input_file, output_dir):
    if not input_file:
        print("Error: No input file specified.")
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
                replace_choice = input(f"The file {treat_filename} already exists. Do you want to replace it? (yes/no/all) ")
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
                print(f".treat file created or replaced: {treat_filename}")

        except json.JSONDecodeError:
            print(f"JSON format error in the line: {line.strip()}")

    return treat_files, temp_dir

def main():
    try:
        dataframe = load_and_validate_csv(csv_path)
        txt_file = generate_test_txt(dataframe, "test.txt")
        treat_files, temp_dir = create_treat_files(txt_file, output_dir)

        if treat_files:
            choice = input("Do you want to import the .treat files into SEAL? (yes/no) ")
            if choice.lower() == 'yes':
                for treat_file in treat_files:
                    token_file = os.path.basename(treat_file).replace('.treat', '.token')
                    token_path = os.path.join(output_dir, token_file)
                    try:
                        shutil.move(treat_file, token_path)
                        print(f"File imported into SEAL: {token_path}")
                    except FileNotFoundError:
                        print(f"Error moving file: {treat_file}")

            else:
                print(f"The .treat files have been stored in: {temp_dir}")
        
        shutil.rmtree(temp_dir)

    except ValueError as e:
        print(e)

############____MAIN____############

if __name__ == "__main__":
    main()
    print("Operation completed.")
    sys.exit(0)