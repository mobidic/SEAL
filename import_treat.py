import json
import os

def create_treat_files(input_file, output_dir):
    # Liste pour stocker les chemins des fichiers .treat créés
    treat_files = []

    # Ouvrir le fichier d'entrée et lire chaque ligne
    with open(input_file, 'r') as file:
        for line in file:
            # Convertir la ligne JSON en dictionnaire
            data = json.loads(line)
            samplename = data["samplename"]
            runname = data["run"]["name"]
            # Créer le nom du fichier .treat
            filename = f"{samplename}-{runname}.treat"
            filepath = os.path.join(output_dir, filename)

            # Écrire les données dans le fichier .treat
            with open(filepath, 'w') as treat_file:
                treat_file.write(line)

            # Ajouter le chemin du fichier à la liste
            treat_files.append(filepath)

    return treat_files

def main():
    # Demander à l'utilisateur le chemin du fichier d'entrée et le répertoire de sortie
    input_file = input("Entrez le chemin du fichier d'entrée .txt : ")
    output_dir = input("Entrez le chemin du répertoire de sortie : ")

    # Vérifier si le répertoire de sortie existe, sinon le créer
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Créer les fichiers .treat
    treat_files = create_treat_files(input_file, output_dir)

    # Demander à l'utilisateur s'il veut renommer les fichiers pour l'importation dans SEAL
    choice = input("Voulez-vous importer les fichiers .treat dans SEAL ? (y/n) : ").lower()
    if choice == 'y':
        for file in treat_files:
            new_name = file.replace('.treat', '.token')
            os.rename(file, new_name)
        print("Les fichiers ont été renommés en .token et sont prêts à être importés.")

if __name__ == "__main__":
    main()