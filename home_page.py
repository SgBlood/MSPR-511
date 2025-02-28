
#+---------------------------------------------+#
#|                                             |#
#|                  IMPORTS                    |#
#|                                             |#
#+---------------------------------------------+#

import re
import tkinter as tk
from tkinter import ttk
import threading
import time
import subprocess
import os
import json
from datetime import datetime
import socket
import tkinter.filedialog as filedialog
import xml.etree.ElementTree as ET
import tkinter.messagebox as messagebox
import requests


#+---------------------------------------------+#
#|                                             |#
#|                  SETUP                      |#
#|                                             |#
#+---------------------------------------------+#

class ApplicationSeahawks:
    def __init__(self, master):
        self.master = master
        self.master.title("Seahawks Harvester")
        self.master.geometry("600x800")
        self.master.minsize(400, 600)
        self.resultats_scan_data = {}
        self.scan_process = None  # Processus de scan
        self.hotes_scannes = []

        # Initialiser thread_running à False pour indiquer qu'aucun scan n'est en cours
        self.thread_running = False

        # Créer le dossier 'scan' si il n'existe pas
        self.scan_dir = "scan"
        if not os.path.exists(self.scan_dir):
            os.makedirs(self.scan_dir)

        # Créer le notebook pour les onglets
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Cadres pour chaque onglet
        self.cadre_accueil = tk.Frame(self.notebook, bg="#212121")
        self.cadre_tableau_de_bord = tk.Frame(self.notebook, bg="#212121")
        self.cadre_ping = tk.Frame(self.notebook, bg="#212121")

        # Ajouter des onglets (frames) au notebook
        self.notebook.add(self.cadre_accueil, text="Accueil")
        self.notebook.add(self.cadre_tableau_de_bord, text="Tableau de bord")
        self.notebook.add(self.cadre_ping, text="Ping")

        # Section Accueil
        self._setup_accueil()

        # Section Tableau de bord
        self._setup_tableau_de_bord()

        # Section Ping
        self._setup_ping()

        # Afficher les fichiers de scan dès le démarrage
        self.afficher_fichiers_scan()   

        self.root = root
        self.master.protocol("WM_DELETE_WINDOW", self.fermer_application)
        
    def _setup_accueil(self):
        """Configure le contenu de l'onglet Accueil."""
        label_nom_entreprise = tk.Label(self.cadre_accueil, text="NFL IT", font=("Arial", 24, "bold"), fg="white", bg="#212121")
        label_nom_entreprise.pack(pady=20)

        self.bouton_scanner = ttk.Button(self.cadre_accueil, text="Scanner", command=self.scanner_reseau_avec_progression)
        self.bouton_scanner.pack(pady=20)

        self.resultats_scan = tk.Text(self.cadre_accueil, height=10, width=80, wrap=tk.WORD, bg="#f4f4f4", fg="black", font=("Arial", 12))
        self.resultats_scan.pack(padx=10, pady=10)

        self.bouton_stop = ttk.Button(self.cadre_accueil, text="Stop Scan", command=self.arreter_scan)
        self.bouton_stop.pack(pady=10)

        # Ajouter le label pour afficher la durée du scan
        self.label_duree_scan = tk.Label(self.cadre_accueil, text="Durée: 00:00", font=("Arial", 12), fg="white", bg="#212121")
        self.label_duree_scan.pack(pady=10)

        # Ajouter le label de version sous les autres éléments
        self.label_version = tk.Label(self.cadre_accueil, text="Version: récupération...", font=("Arial", 10), fg="white", bg="#212121")
        self.label_version.pack(pady=5)

        # Lancer la récupération de la version dans un thread pour ne pas bloquer l'interface
        threading.Thread(target=self.update_version_label, daemon=True).start()

    def _setup_tableau_de_bord(self):
        """Configure le contenu de l'onglet Tableau de bord."""
        self.tableau_de_bord_text = tk.Text(self.cadre_tableau_de_bord, height=20, width=80, wrap=tk.WORD, bg="#f4f4f4", fg="black", font=("Arial", 12))
        self.tableau_de_bord_text.pack(padx=10, pady=10)

        # Boutons
        self.bouton_refresh = ttk.Button(self.cadre_tableau_de_bord, text="Rafraîchir", command=self.refresh_fichiers_scan)
        self.bouton_refresh.pack(pady=5)

        self.bouton_telecharger = ttk.Button(self.cadre_tableau_de_bord, text="Télécharger", command=self.telecharger_resultat)
        self.bouton_telecharger.pack(pady=5)

        self.bouton_retour = ttk.Button(self.cadre_tableau_de_bord, text="Retour", command=self.retour_tableau_de_bord)
        self.bouton_retour.pack(pady=5)

        # Ajout d'un label pour afficher les infos de l'hôte sous les boutons
        self.label_host_info = tk.Label(self.cadre_tableau_de_bord, text="", font=("Arial", 12), bg="#212121", fg="white")
        self.label_host_info.pack(pady=10)
        
        # Met à jour le label avec l'IP locale et le nom de l'hôte
        self.update_host_info()

    def _setup_ping(self):
        """Configure le contenu de l'onglet Ping."""
        self.label_ping = tk.Label(self.cadre_ping, text="Ping une cible", font=("Arial", 16, "bold"))
        self.label_ping.pack(pady=10)

        self.entry_target = tk.Entry(self.cadre_ping, font=("Arial", 12), width=30)
        self.entry_target.pack(pady=10)
        self.entry_target.insert(0, "Entrez une IP ou un hôte")  # Texte par défaut
        self.entry_target.bind("<FocusIn>", self.clear_placeholder)

        self.bouton_ping = ttk.Button(self.cadre_ping, text="Ping", command=self.ping_target)
        self.bouton_ping.pack(pady=10)

        self.bouton_stop_ping = ttk.Button(self.cadre_ping, text="Stop Ping", command=self.stop_ping, state="disabled")
        self.bouton_stop_ping.pack(pady=10)

        self.resultats_ping = tk.Text(self.cadre_ping, height=10, width=50, wrap=tk.WORD, bg="#f4f4f4", fg="black", font=("Arial", 12))
        self.resultats_ping.pack(padx=10, pady=10)

        # Section pour sélectionner un fichier JSON et récupérer les IPs
        self.bouton_choisir_fichier = ttk.Button(self.cadre_ping, text="Choisir un fichier JSON", command=self.choisir_fichier_json)
        self.bouton_choisir_fichier.pack(pady=10)

        self.combo_ip = ttk.Combobox(self.cadre_ping, font=("Arial", 12), width=30)
        self.combo_ip.pack(pady=10)

        # Ajouter bouton pour supprimer les hôtes
        self.bouton_supprimer_hotes = ttk.Button(self.cadre_ping, text="Supprimer les hôtes", command=self.supprimer_hotes)
        self.bouton_supprimer_hotes.pack(pady=10)

    def fermer_application(self):
        """Gère la fermeture de la fenêtre, arrête tous les processus et ferme proprement l'application."""
        if self.thread_running:
            # Si un scan est en cours, tuer le processus de scan
            if hasattr(self, 'scan_process') and self.scan_process:
                self.scan_process.terminate()  # Tuer le processus de scan
            # Si un thread est en cours, attendre qu'il se termine
            if hasattr(self, 'scan_thread') and self.scan_thread.is_alive():
                self.scan_thread.join()

            # Vous pouvez ajouter ici d'autres processus à arrêter si nécessaire, comme ping_process

            # Marquer que le thread est terminé
            self.thread_running = False

        # Fermer la fenêtre principale
        self.master.quit()  # Quitter la boucle principale Tkinter
        self.master.destroy()  # Détruire l'interface graphique pour nettoyer les ressources

    def update_host_info(self):
        """Met à jour et affiche les informations de l'hôte (nom et IP locale)."""
        local_ip = self.obtenir_ip_locale()
        hostname = socket.gethostname()
        self.label_host_info.config(text=f"Nom de l'hôte : {hostname} | Adresse IP locale : {local_ip}")

    def update_version_label(self):
        """Récupère la version via l'API GitHub et met à jour le label."""
        try:
            url = "https://api.github.com/repos/SgBlood/MSPR-511/releases/latest"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Le tag se trouve dans data["tag_name"]
                # Le titre de la release se trouve dans data["name"]
                release_title = data.get("name", "Inconnue")
            else:
                release_title = "Non disponible (code HTTP: {})".format(response.status_code)
        except Exception as e:
            release_title = f"Erreur: {e}"
        
        self.master.after(0, lambda: self.label_version.config(text=f"Version: {release_title}"))

#+---------------------------------------------+#
#|                                             |#
#|                   PING                      |#
#|                                             |#
#+---------------------------------------------+#

    def ping_target(self):
        """Ping l'adresse cible, soit via l'input, soit via l'IP choisie dans le combobox."""
        target = self.entry_target.get()
        if target == "Entrez une IP ou un hôte" and not self.combo_ip.get():
            self.resultats_ping.insert(tk.END, "Veuillez entrer une cible ou choisir une IP dans la liste.\n")
            return

        if not target or target == "Entrez une IP ou un hôte":
            target = self.combo_ip.get()

        self.resultats_ping.delete(1.0, tk.END)
        self.resultats_ping.insert(tk.END, f"Ping de {target}...\n")

        # Désactiver le bouton Ping et activer le bouton Stop
        self.bouton_ping.config(state="disabled")
        self.bouton_stop_ping.config(state="normal")

        # Exécution de la commande ping via subprocess
        self.ping_process = subprocess.Popen(["ping", "-t", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Lire les résultats en temps réel sans bloquer l'interface Tkinter
        self.ping_thread = threading.Thread(target=self.lire_resultats_ping)
        self.ping_thread.start()
    
    def stop_ping(self):
        """Arrêter le ping en cours."""
        if self.ping_process:
            self.ping_process.terminate()
            self.ping_process.wait()

        # Réactiver le bouton Ping et désactiver le bouton Stop
        self.bouton_ping.config(state="normal")
        self.bouton_stop_ping.config(state="disabled")

        self.resultats_ping.insert(tk.END, "\nPing arrêté.\n")

    def clear_placeholder(self, event):
        """Efface le texte placeholder lorsque l'utilisateur clique dans le champ."""
        if self.entry_target.get() == "Entrez une IP ou un hôte":
            self.entry_target.delete(0, tk.END)

    def choisir_fichier_json(self):
        """Permet de choisir un fichier JSON contenant les IPs à pinger."""
        fichier_json = filedialog.askopenfilename(initialdir=self.scan_dir, title="Choisir un fichier JSON",
        filetypes=(("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")))
        if fichier_json:
            self.extraire_ips_du_fichier_json(fichier_json)

    def extraire_ips_du_fichier_json(self, fichier_json):
        """Extrait les IPs d'un fichier JSON et les ajoute dans le combobox."""
        try:
            with open(fichier_json, 'r', encoding="utf-8") as file:
                data = json.load(file)
                # Si data est une liste, itérer directement dessus
                if isinstance(data, list):
                    ips = [host['ip'] for host in data if 'ip' in host]
                else:
                    # Sinon, essayer d'extraire la liste à partir de la clé 'hosts'
                    ips = [host['ip'] for host in data.get('hosts', []) if 'ip' in host]
                if ips:
                    self.combo_ip['values'] = ips
                    self.combo_ip.set(ips[0])  # Sélectionner automatiquement la première IP
                else:
                    self.resultats_ping.insert(tk.END, "Aucune IP trouvée dans le fichier JSON.\n")
        except Exception as e:
            self.resultats_ping.insert(tk.END, f"Erreur lors de l'extraction des IPs: {e}\n")

    def supprimer_hotes(self):
        """Supprime les hôtes du combo box."""
        self.combo_ip.set("")
        self.combo_ip['values'] = []

    def lire_resultats_ping(self):
        """Lit les résultats du ping en temps réel et affiche un résumé des statistiques."""
        all_lines = []
        try:
            for line in self.ping_process.stdout:
                # Affichage en temps réel dans le Text widget (UTF-8 par défaut)
                self.resultats_ping.insert(tk.END, line)
                self.resultats_ping.see(tk.END)
                all_lines.append(line)
        except Exception as e:
            self.resultats_ping.insert(tk.END, f"\nErreur lors de la lecture du ping: {e}\n")
        
        # Une fois le ping terminé, parser le résumé
        summary_info = self.parse_ping_summary(all_lines)
        if summary_info:
            summary_text = "\nStatistiques du ping :\n"
            summary_text += f"Paquets envoyés : {summary_info.get('sent', 'N/A')}\n"
            summary_text += f"Paquets reçus  : {summary_info.get('received', 'N/A')}\n"
            summary_text += f"Packet loss    : {summary_info.get('loss', 'N/A')}\n"
            summary_text += f"Temps minimum  : {summary_info.get('min', 'N/A')}\n"
            summary_text += f"Temps maximum  : {summary_info.get('max', 'N/A')}\n"
            summary_text += f"Temps moyen    : {summary_info.get('avg', 'N/A')}\n"
            self.resultats_ping.insert(tk.END, summary_text)

    def parse_ping_summary(self, lines):
        """
        Analyse les lignes de sortie du ping pour extraire les statistiques.
        Supporte à la fois les formats en anglais et en français.
        """
        summary = {}
        for line in lines:
            # Recherche de la ligne de statistiques des paquets
            if (("Sent" in line and "Received" in line and "Lost" in line) or 
                ("Envoyés" in line and "Reçus" in line and "Perdus" in line)):
                # Exemple en anglais :
                #   "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
                # Exemple en français :
                #   "Paquets : Envoyés = 4, Reçus = 4, Perdus = 0 (0% de perte)"
                m = re.search(r"(?:Sent|Envoyés)\s*=\s*(\d+)[^,]*,\s*(?:Received|Reçus)\s*=\s*(\d+)[^,]*,\s*(?:Lost|Perdus)\s*=\s*(\d+).*?(\d+)%", line)
                if m:
                    summary['sent'] = m.group(1)
                    summary['received'] = m.group(2)
                    summary['lost'] = m.group(3)
                    summary['loss'] = m.group(4) + "%"
            # Recherche de la ligne de statistiques des temps
            if (("Minimum" in line and "Maximum" in line and ("Average" in line or "Moyenne" in line))):
                # Exemple en anglais :
                #   "Minimum = 1ms, Maximum = 2ms, Average = 1ms"
                # Exemple en français :
                #   "Minimum = 1ms, Maximum = 2ms, Moyenne = 1ms"
                m2 = re.search(r"(?:Minimum)\s*=\s*(\d+)[^\d]+(?:Maximum)\s*=\s*(\d+)[^\d]+(?:Average|Moyenne)\s*=\s*(\d+)", line)
                if m2:
                    summary['min'] = m2.group(1) + "ms"
                    summary['max'] = m2.group(2) + "ms"
                    summary['avg'] = m2.group(3) + "ms"
        return summary

#+---------------------------------------------+#
#|                                             |#
#|             Tableau de bord                 |#
#|                                             |#
#+---------------------------------------------+#

    def afficher_fichiers_scan(self):
        """Affiche uniquement la liste des fichiers disponibles dans le tableau de bord."""
        self.tableau_de_bord_text.delete(1.0, tk.END)
        
        # On ne met plus les infos de l'hôte ici, elles sont désormais affichées dans le label dédié.
        
        fichiers_scan = [f for f in os.listdir(self.scan_dir) if f.endswith(".txt")]
        if fichiers_scan:
            self.tableau_de_bord_text.insert(tk.END, "Fichiers disponibles :\n")
            for fichier in fichiers_scan:
                bouton_fichier = tk.Button(self.tableau_de_bord_text, text=fichier, command=lambda f=fichier: self.consulter_fichier(f))
                self.tableau_de_bord_text.window_create(tk.END, window=bouton_fichier)
                self.tableau_de_bord_text.insert(tk.END, "\n")
        else:
            self.tableau_de_bord_text.insert(tk.END, "Aucun fichier de scan trouvé.\n")

    def consulter_fichier(self, fichier_choisi):
        """Ouvre un fichier de scan spécifique et affiche son contenu dans la fenêtre tableau de bord."""
        try:
            with open(os.path.join(self.scan_dir, fichier_choisi), 'r', encoding="utf-8") as f:
                contenu = f.read()
                self.tableau_de_bord_text.delete(1.0, tk.END)  # Effacer le contenu précédent
                self.tableau_de_bord_text.insert(tk.END, contenu)
        except Exception as e:
            print(f"Erreur lors de la consultation du fichier: {e}")
            
    def retour_tableau_de_bord(self):
        """Retourne à la vue principale du tableau de bord."""
        self.afficher_fichiers_scan()

    def refresh_fichiers_scan(self):
        """Met à jour la liste des fichiers de scan."""
        self.afficher_fichiers_scan()

    def telecharger_resultat(self):
        """Permet de télécharger les résultats du scan."""
        fichiers_scan = [f for f in os.listdir(self.scan_dir) if f.endswith(".txt") or f.endswith(".json")]
        if fichiers_scan:
            fichier_choisi = filedialog.askopenfilename(initialdir=self.scan_dir, title="Télécharger un fichier", 
            filetypes=(("Fichiers texte", "*.txt"), ("Fichiers JSON", "*.json")))
            if fichier_choisi:
                # Copier le fichier dans un répertoire de téléchargement
                try:
                    destination = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Tous les fichiers", "*.*")])
                    if destination:
                        with open(fichier_choisi, 'r', encoding="utf-8") as f_in:
                            content = f_in.read()
                            with open(destination, 'w', encoding="utf-8") as f_out:
                                f_out.write(content)
                        print(f"Fichier téléchargé vers: {destination}")
                except Exception as e:
                    print(f"Erreur lors du téléchargement: {e}")
        else:
            print("Aucun fichier de scan à télécharger.")

#+---------------------------------------------+#
#|                                             |#
#|                   SCAN                      |#
#|                                             |#
#+---------------------------------------------+#

    def obtenir_ip_locale(self):
        """Récupère l'adresse IP locale de l'hôte."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip_locale = s.getsockname()[0]
            s.close()
            return ip_locale
        except Exception as e:
            self.resultats_scan.insert(tk.END, f"Erreur lors de la récupération de l'IP locale: {e}\n")
            return None

    def lire_resultats_scan(self, json_filename, txt_filename):
        """Lit les résultats en direct, extrait les infos et génère directement JSON/TXT, avec le temps par hôte."""
        scan_results = []
        host_info = None

        for line in self.scan_process.stdout:
            self.resultats_scan.insert(tk.END, line)
            self.resultats_scan.see(tk.END)

            # Détecter une nouvelle adresse IP
            match_ip = re.search(r"Nmap scan report for (\S+)", line)
            if match_ip:
                # Si on passe à un nouvel hôte, on calcule la durée du scan de l'hôte précédent
                if host_info:
                    host_info['duration'] = time.time() - host_info['start_time']
                    scan_results.append(host_info)
                    # Sauvegarde en temps réel (vous pouvez choisir de sauvegarder à chaque nouvel hôte ou à la fin)
                    self.sauvegarder_resultats_scan(scan_results, json_filename, txt_filename)
                # Démarrage d'un nouvel hôte avec enregistrement du temps de départ
                host_info = {"ip": match_ip.group(1), "ports": []}
                host_info['start_time'] = time.time()

            match_port = re.search(r"(\d+)/tcp\s+open\s+(\S+)(?:\s+(.*))?", line)
            if match_port and host_info:
                port_info = {
                    "port": match_port.group(1),
                    "service": match_port.group(2),
                    "state": "open",
                    "version": match_port.group(3).strip() if match_port.group(3) else "Inconnue"
                }
                host_info["ports"].append(port_info)

        # Ajout du dernier hôte traité
        if host_info:
            host_info['duration'] = time.time() - host_info['start_time']
            scan_results.append(host_info)
            self.sauvegarder_resultats_scan(scan_results, json_filename, txt_filename)

        self.resultats_scan.insert(tk.END, "\nScan terminé.\n")
        self.thread_running = False
        # Affichage d'une popup et rafraîchissement du tableau de bord
        self.master.after(0, self.scan_finished)

    def scan_finished(self):
        """Affiche une popup pour informer que le scan est terminé et rafraîchit le tableau de bord."""
        messagebox.showinfo("Scan terminé", "Le scan est terminé.")
        self.afficher_fichiers_scan()  # Rafraîchit la liste des fichiers du tableau de bord    
    
    def scanner_reseau_avec_progression(self):
        """Démarre un scan réseau avec détection d'OS et des services et sauvegarde JSON/TXT directement."""
        if self.thread_running:
            self.resultats_scan.insert(tk.END, "\nScan déjà en cours, veuillez attendre qu'il se termine.\n")
            return

        self.resultats_scan.delete(1.0, tk.END)
        self.hotes_scannes = []
        self.thread_running = True
        self.resultats_scan.insert(tk.END, "Démarrage du scan...\n")

        self.scan_start_time = time.time()

        ip_locale = self.obtenir_ip_locale()
        if ip_locale is None:
            return

        reseau = '.'.join(ip_locale.split('.')[:3]) + '.0/24'

        timestamp = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
        scan_dir = self.scan_dir  # Assurez-vous que scan_dir est défini
        json_filename = os.path.join(scan_dir, f"scan_results_{timestamp}.json")
        txt_filename = os.path.join(scan_dir, f"scan_results_{timestamp}.txt")

        try:
            self.scan_process = subprocess.Popen(
                ["nmap", "-A", "-O", "-sV", "-T4", reseau],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            self.resultats_scan.insert(tk.END, f"\nErreur lors du démarrage du scan : {e}\n")
            self.thread_running = False
            return

        self.scan_thread = threading.Thread(target=self.lire_resultats_scan, args=(json_filename, txt_filename))
        self.scan_thread.start()
        self.timer_thread = threading.Thread(target=self.mettre_a_jour_duree)
        self.timer_thread.start()
            
    def sauvegarder_resultats_scan(self, scan_results, json_filename, txt_filename):
        """Sauvegarde les résultats du scan en JSON et TXT."""
        try:
            if not os.path.exists(self.scan_dir):
                os.makedirs(self.scan_dir)

            # Sauvegarde en JSON
            with open(json_filename, 'w', encoding='utf-8') as json_f:
                json.dump(scan_results, json_f, indent=4)

            # Sauvegarde en TXT
            with open(txt_filename, 'w', encoding='utf-8') as txt_f:
                txt_f.write(f"Scan complet {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                # Temps total du scan (si vous avez enregistré self.scan_start_time)
                total_duration = time.time() - self.scan_start_time
                txt_f.write(f"Durée totale du scan: {total_duration:.2f} secondes\n")
                for host in scan_results:
                    txt_f.write(f"\nIP: {host.get('ip', 'Inconnu')}\n")
                    if 'duration' in host:
                        txt_f.write(f"Durée du scan pour cet hôte: {host['duration']:.2f} secondes\n")
                    txt_f.write("Ports ouverts et services:\n")
                    for port in host.get('ports', []):
                        txt_f.write(f" - Port: {port.get('port', 'Inconnu')} ({port.get('protocol', 'Inconnu')})\n")
                        txt_f.write(f"   État: {port.get('state', 'Inconnu')}\n")
                        txt_f.write(f"   Service: {port.get('service', 'Inconnu')} | Version: {port.get('version', 'Inconnu')} | Produit: {port.get('product', 'Inconnu')}\n")

            self.resultats_scan.insert(tk.END, f"\nLes résultats du scan sont enregistrés dans {json_filename} et {txt_filename}\n")
        except Exception as e:
            self.resultats_scan.insert(tk.END, f"\nErreur lors de la sauvegarde des résultats: {e}\n")
    
    def verifier_scan_termine(self, json_filename, txt_filename):
        """Vérifie si le scan est terminé et gère la fin du processus."""
        while self.thread_running:
            if self.scan_process.poll() is not None:
                self.thread_running = False
                self.resultats_scan.insert(tk.END, "\nScan terminé.\n")
                # Sauvegarde des résultats en JSON et TXT
                self.sauvegarder_resultats_scan(self.hotes_scannes, json_filename, txt_filename)
                break
            time.sleep(0.1)  # Vérifier toutes les 0.5 secondes
        
    def mettre_a_jour_duree(self):
        """Cette méthode met à jour l'affichage de la durée écoulée du scan avec les millisecondes."""
        while self.thread_running:  # Tant que le scan est en cours
            elapsed_time = time.time() - self.scan_start_time
            minutes, seconds = divmod(elapsed_time, 60)
            seconds = int(seconds)
            milliseconds = int((elapsed_time - seconds) * 1000)  # Extraire les millisecondes
            
            # Mise à jour du label avec la durée du scan, formatée en mm:ss:ms
            self.label_duree_scan.config(text=f"Durée: {int(minutes):02}:{seconds:02}:{milliseconds:03}")
            
            time.sleep(0.01)  # Met à jour toutes les 10 millisecondes pour un affichage fluide
            
    def arreter_scan(self):
        """Arrête le scan en cours."""
        if hasattr(self, 'scan_process') and self.scan_process:
            self.scan_process.terminate()
            self.resultats_scan.insert(tk.END, "\nScan arrêté.\n")
            self.thread_running = False

#+---------------------------------------------+#
#|                                             |#
#|                  END                        |#
#|                                             |#
#+---------------------------------------------+#

# Création de la fenêtre principale et lancement de l'application
root = tk.Tk()
app = ApplicationSeahawks(root)
root.mainloop()
