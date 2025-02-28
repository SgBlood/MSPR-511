import os
import subprocess
import requests
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import sys

# Charger les variables d'environnement
load_dotenv()

# Configurations GitLab
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "67561997")  # ID réel du projet GitLab
GITLAB_API_RELEASES_URL = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/releases"
GITLAB_REPO_URL = "https://gitlab.com/mspr-5111/Seahawks_Harvester.git"
LOCAL_VERSION_FILE = "version.txt"

def get_latest_gitlab_version():
    """Récupère la dernière version publiée sur GitLab Releases et rejette une version invalide (0.0.0 ou 0)."""
    headers = {"PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN")}
    try:
        response = requests.get(GITLAB_API_RELEASES_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                version = data[0]["tag_name"].strip()  # Ex: "v1.0.1"
                if version in ["0", "0.0.0"]:
                    print("❌ Version distante invalide (0.0.0).")
                    return None
                return version
        print(f"❌ Erreur GitLab (Code: {response.status_code}): {response.text}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des releases GitLab: {e}")
        return None

def get_local_version():
    """Lit la version locale depuis version.txt et rejette une valeur vide ou égale à zéro."""
    if os.path.exists(LOCAL_VERSION_FILE):
        try:
            with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
                version = f.readline().strip()  # Lire la première ligne
                if not version or version in ["0", "0.0.0"]:
                    print("❌ Version locale invalide (vide ou zéro).")
                    return None
                return version
        except Exception as e:
            print(f"❌ Erreur lecture version.txt : {e}")
            return None
    return None

def compare_versions(local_version, latest_version):
    """Compare les versions sous forme de tuples pour s'assurer que la version locale n'est pas supérieure."""
    try:
        local_tuple = tuple(map(int, local_version.lstrip('v').split('.')))
        latest_tuple = tuple(map(int, latest_version.lstrip('v').split('.')))
        if local_tuple > latest_tuple:
            print(f"❌ Version locale {local_version} ne peut pas être supérieure à la version distante {latest_version}.")
            return False
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la comparaison des versions : {e}")
        return False

def update_application():
    """Met à jour l'application via Git et informe l'utilisateur que la mise à jour est terminée."""
    print("\n🔄 Téléchargement et application de la mise à jour...\n")
    try:
        subprocess.run(["git", "fetch", "--all"], check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        subprocess.run(["git", "pull", "origin", "main"], check=True)

        # Mise à jour du fichier version.txt
        latest_version = get_latest_gitlab_version()
        if latest_version:
            with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(latest_version)

        print("\n✅ Mise à jour terminée.")
        messagebox.showinfo("Mise à jour", "✅ Mise à jour terminée ! Veuillez relancer l'application.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de la mise à jour : {e}")
        messagebox.showerror("Erreur", f"❌ Erreur lors de la mise à jour : {e}")

def check_for_update():
    """Vérifie la version et, si une mise à jour est nécessaire, la propose à l'utilisateur."""
    latest_version = get_latest_gitlab_version()
    local_version = get_local_version()
    
    # Si la version locale est invalide, forcer la mise à jour
    if not local_version:
        print("❌ Impossible de récupérer une version locale valide. Mise à jour forcée.")
        update_application()
        return
    
    # Si la version distante est invalide, afficher une erreur
    if not latest_version:
        messagebox.showerror("Erreur", "La version distante est invalide (0.0.0 ou absente).")
        return

    if latest_version and local_version:
        if not compare_versions(local_version, latest_version):
            messagebox.showerror("Erreur de version", f"❌ Version locale {local_version} incorrecte.\nVeuillez réinstaller l'application.")
            return
        
        if local_version != latest_version:
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale Tkinter
            response = messagebox.askyesno(
                "Mise à jour disponible",
                f"🚀 Nouvelle version détectée : {latest_version}\nActuelle : {local_version}\n\nVoulez-vous mettre à jour ?"
            )
            if response:
                update_application()
            else:
                print("❌ Mise à jour annulée.")
        else:
            print("\n✅ L'application est à jour.")

# Exécuter la vérification de mise à jour au lancement
check_for_update()
