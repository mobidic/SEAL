import json
import os
import sys
import shutil
import tempfile

# Fonction pour créer un fichier .treat avec gestion des doublons
def create_treat_file(data, output_dir, replace_all):
    samplename = data['samplename']
    run_name = data['run']['name']
    treat_filename = os.path.join(output_dir, f"{samplename}-{run_name}.treat")

    if os.path.exists(treat_filename) and replace_all is None:
        replace_choice = input(f"Le fichier {treat_filename} existe déjà. Voulez-vous le remplacer ? (oui/non/tous) ")
        if replace_choice.lower() == 'tous':
            replace_all = True
        elif replace_choice.lower() == 'non':
            i = 1
            while os.path.exists(f"{treat_filename}({i})"):
                i += 1
            treat_filename = f"{treat_filename}({i})"
            replace_all = False
    return treat_filename, replace_all

# Fonction principale pour créer les fichiers .treat
def create_treat_files(input_file, output_dir):
    if not input_file:
        print("Erreur : Aucun fichier d'entrée spécifié.")
        return [], ""

    temp_dir = tempfile.mkdtemp(dir=os.path.dirname(output_dir))
    treat_files = []
    replace_all = None

    with open(input_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        try:
            data = json.loads(line.strip())
            treat_filename, replace_all = create_treat_file(data, temp_dir, replace_all)

            with open(treat_filename, 'w') as treat_file:
                treat_file.write(line.strip())
                treat_files.append(treat_filename)
                print(f"Fichier .treat créé ou remplacé : {treat_filename}")

        except json.JSONDecodeError:
            print(f"Erreur de format JSON dans la ligne : {line.strip()}")

    return treat_files, temp_dir

# Point d'entrée du script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_treat.py <fichier.txt>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = os.path.expanduser("~/Bureau/SEAL/seal/static/temp/vcf")
    treat_files, temp_dir = create_treat_files(input_file, output_dir)

    # Importer ou non les fichiers dans SEAL
    if treat_files:
        choice = input("Voulez-vous importer les fichiers .treat dans SEAL ? (oui/non) ")

        if choice.lower() == 'oui':
            for treat_file in treat_files:
                token_file = os.path.basename(treat_file).replace('.treat', '.token')
                token_path = os.path.join(output_dir, token_file)
                try:
                    os.rename(treat_file, token_path)
                    print(f"Fichier importé dans SEAL : {token_path}")
                except FileNotFoundError:
                    pass # comme le token est instantanément utilisé dès sa création, le système n'a pas le temps de le voir lorsqu'il le check et renvoie une erreur à tord

            shutil.rmtree(temp_dir)
        else:
            print(f"Les fichiers .treat ont été stockés dans : {temp_dir}")

        print("Opération terminée.")
        sys.exit(0)