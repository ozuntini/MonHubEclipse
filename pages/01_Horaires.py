#!/usr/bin/env python3
"""
Programme Python permettant de créer ou de modifier un script d'ordonnancement utilisé par Solar_Eclipse_Photography.
Ce script utilise Streamlit pour l'interface utilisateur, et permet de saisir les heures des différentes étapes de l'éclipse (C1, C2, Max, C3, C4).
Il offre également la possibilité de charger un fichier existant, de faire une copie de sécurité avant d'écraser un fichier, et de conserver les lignes déjà présentes dans le fichier si besoin.
"""
import streamlit as st
import os
from shutil import copy2
from datetime import time, datetime
import plotly.graph_objects as go
import logging

# Configuration du logger
log_file = "app_activity.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

st.set_page_config(page_title="Horaires", page_icon="🕔", layout="wide")

DOSSIERS_FAVORIS = {
    "📁 Répertoire local": os.getcwd(),
    "🗂️ Archives": "/home/ozuntini/Documents/Eclipses/archives_Scripts",
    "🇪🇸 Espagne 2026": "/home/ozuntini/Documents/Eclipses/Spain2026/Scripts",
    "🇪🇬 Égypte 2027": "/home/ozuntini/Documents/Eclipses/Egypt2027/Scripts",
    "💾 Sauvegarde Réseau": "/home/ozuntini/Public",
    "➕ Autre...": "CUSTOM"
}

DEFAULT_TOWN = "Niort"
DEFAULT_DATE = datetime.now()
DEFAULT_FILE_HEADER = "./ScriptHeader.txt"
DEFAULT_CONFIG = "# Ligne de configuration principale \n# Config,C1,C2,Max,C3,C4 \n# C1 = Premier contact, C2 = Début totalité, Max = Maximum, C3 = Fin totalité, C4 = Dernier contact"
DEFAULT_ACTION_CONFIG = "Config,"

# Lecture du header par défaut
try:
    with open(DEFAULT_FILE_HEADER, "r", encoding="utf-8") as f:
        DEFAULT_HEADER = f.readlines()
        logging.info(f"SUCCÈS: Header par défaut chargé depuis {DEFAULT_FILE_HEADER}")
except Exception as e:
    logging.error(f"ERREUR: Impossible de charger le header par défaut : {e}")
    DEFAULT_HEADER = ["# Fichier de description de l'ordonnancement des actions",
                      "# Ce fichier est destiné à être lu par le script d'ordonnancement pour déclencher les actions aux heures spécifiées."
    ]

# Initialisation des valeurs par défaut pour les heures (H, M, S)
for p in ["C1", "C2", "Max", "C3", "C4"]:
    if f"{p}_h" not in st.session_state:
        st.session_state[f"{p}_h"] = 8
        st.session_state[f"{p}_m"] = 0
        st.session_state[f"{p}_s"] = 0

if "lieu" not in st.session_state:
    st.session_state["lieu"] = DEFAULT_TOWN
if "date_saisie" not in st.session_state:
    st.session_state["date_saisie"] = DEFAULT_DATE

# --- 1. CONFIGURATION ET MÉMOIRE ---
if "chemin_manuel" not in st.session_state:
    st.session_state["chemin_manuel"] = ""

# --- 2. FONCTIONS DE GESTION ---
def vider_chemin():
    """Efface la saisie manuelle dans la mémoire de session."""
    st.session_state["chemin_manuel"] = ""

# --- 3. FONCTIONS DE CHARGEMENT ---
def charger_fichier_existant(chemin_complet, nom_du_fichier):
    try:
        # --- A. Extraire le Lieu et la Date du NOM du fichier ---
        # On enlève l'extension .txt et on sépare par le tiret
        nom_sans_ext = nom_du_fichier.replace(".txt", "")
        if "-" in nom_sans_ext:
            lieu_extrait, date_extraite_str = nom_sans_ext.split("-", 1)
            st.session_state["lieu"] = lieu_extrait
            # Conversion de la chaîne JJ_MM_AAAA en objet date
            st.session_state["date_saisie"] = datetime.strptime(date_extraite_str, "%d_%m_%Y")
            logging.info(f"SUCCÈS: Lieu et date extraits du nom du fichier : {lieu_extrait}, {date_extraite_str}")
        else:
            logging.warning(f"AVERTISSEMENT: Le nom du fichier ne respecte pas le format attendu : {nom_du_fichier}")
            st.warning("Le nom du fichier ne respecte pas le format attendu (Lieu-Date). Les champs Lieu et Date n'ont pas été mis à jour.")

        # --- B. Extraire les Heures du CONTENU du fichier ---
        with open(chemin_complet, "r", encoding="utf-8") as f:
            lignes = f.readlines()
            for ligne in lignes:
                if ligne.startswith("Config,"):
                    donnees = ligne.strip().split(",")
                    del donnees[0]  # Supprimer "Config"
                    params = ["C1", "C2", "Max", "C3", "C4"]
                    for i, p in enumerate(params):
                        h, m, s = map(int, donnees[i].split(":"))
                        st.session_state[f"{p}_h"] = h
                        st.session_state[f"{p}_m"] = m
                        st.session_state[f"{p}_s"] = s
        logging.info(f"SUCCÈS: Fichier chargé : {nom_du_fichier} depuis {chemin_complet}")
        st.success(f"✅ Fichier '{nom_du_fichier}' chargé !")
        return lignes 
    except Exception as e:
        logging.error(f"ERREUR: Impossible de charger le fichier : {e}")
        st.error(f"Erreur d'importation : {e}")

# --- 4. FONCTION DE SAISIE D'HEURE DYNAMIQUE ---
def saisie_heure_dynamique(label):
    """
    Génère 3 sélecteurs numériques. 
    On ne passe plus 'value', Streamlit utilisera automatiquement 
    la valeur stockée dans st.session_state[key].
    """
    st.write(f"**{label}**")
    c_h, c_m, c_s = st.columns(3)
    with c_h: 
        # On supprime 'h_prec', on garde juste la key
        h = st.number_input("H", 0, 23, key=f"{label}_h")
    with c_m: 
        m = st.number_input("M", 0, 59, key=f"{label}_m")
    with c_s: 
        s = st.number_input("S", 0, 59, key=f"{label}_s")
    return time(h, m, s)

# --- 5. FONCTION DE COPIE DE SECURITE DU FICHIER ---
def copier_fichier_securite(chemin_complet):
    """Renome le fichier existant."""
    try:
        if os.path.isfile(chemin_complet):
            nom_base = os.path.basename(chemin_complet)
            nom_sans_ext, ext = os.path.splitext(nom_base)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_sauvegarde = f"{nom_sans_ext}_backup_{timestamp}{ext}"
            chemin_sauvegarde = os.path.join(os.path.dirname(chemin_complet), nom_sauvegarde)
            copy2(chemin_complet, chemin_sauvegarde)
            logging.info(f"SUCCÈS: Copie de sécurité créée : {nom_sauvegarde}")
            st.info(f"⚠️ Une copie de sécurité a été créée : `{nom_sauvegarde}`")
            return "Copie de sécurité créée"
    except Exception as e:
        logging.error(f"ERREUR: Impossible de créer une copie de sécurité : {e}")
        st.error("⚠️ Une erreur est survenue lors de la création de la copie de sécurité.")
        return "Erreur lors de la copie de sécurité"

# --- 6. FONCTION DE CONSERVATION DES LIGNES DEJA EXISTANTES (SI BESOIN) ---
def conserver_lignes_existantes(chemin_complet, debut_ligne_nouvelles_donnees, nouvelles_lignes):
    """Conserve les lignes existantes qui ne sont pas écrasées par les nouvelles données."""
    try:
        if os.path.isfile(chemin_complet):
            with open(chemin_complet, "r", encoding="utf-8") as f:
                lignes_existantes = f.readlines()
                with open(chemin_complet, "w", encoding="utf-8") as f:
                    for ligne in lignes_existantes:
                        if ligne.startswith(debut_ligne_nouvelles_donnees):
                            f.writelines(nouvelles_lignes + "\n")     # Ajoute la nouvelle ligne
                            logging.info(f"SUCCÈS: Ligne existante écrasée par les nouvelles données dans : {chemin_complet}")    
                        else:
                            f.writelines(ligne)  # Conserve les anciennes lignes
                        f.flush()  # Assure que les données sont écrites immédiatement
            logging.info(f"SUCCÈS: Lignes existantes conservées et nouvelles lignes ajoutées dans : {chemin_complet}")
            return "Lignes conservées et mises à jour"
    except Exception as e:
        logging.error(f"ERREUR: Impossible de conserver les lignes existantes : {e}")
        return "Erreur lors de la conservation des lignes"

# --- 7. FONCTION D'ÉCRITURE DANS UN NOUVEAU FICHIER ---
def ecrire_nouveau_fichier(chemin_complet, contenu):
    """Écrit le contenu dans un nouveau fichier."""
    try:
        with open(chemin_complet, "w", encoding="utf-8") as f:
            for ligne in DEFAULT_HEADER:
                f.write(ligne if ligne.endswith("\n") else ligne + "\n")    # Assure que chaque ligne se termine par un saut de ligne
            f.write(DEFAULT_CONFIG + "\n")
            f.write(contenu + "\n")
            f.write("#\n")
            f.flush()  # Assure que les données sont écrites immédiatement
        # On écrit dans le log
        logging.info(f"SUCCÈS: Fichier créé : {nom_fichier} dans {chemin_final}")
        return "Fichier créé"
    except Exception as e:
        logging.error(f"ERREUR: Impossible d'écrire dans le fichier : {e}")
        return "Erreur lors de la création du fichier"

# 1. Fonction pour calculer la différence entre deux objets time
def calculer_duree(t_debut, t_fin):
    # On utilise une date fictive pour le calcul
    dummy_date = datetime.min
    delta = datetime.combine(dummy_date, t_fin) - datetime.combine(dummy_date, t_debut)
    
    # Formatage propre (HHh MMm SSs)
    heures, reste = divmod(delta.seconds, 3600)
    minutes, secondes = divmod(reste, 60)
    if heures == 0 and minutes == 0:
        return f"{secondes:02d}s"
    elif heures == 0:
        return f"{minutes:02d}m {secondes:02d}s"
    return f"{heures:02d}h {minutes:02d}m {secondes:02d}s"


# --- 5. INTERFACE : DESTINATION & LECTURE ---
st.title("😎 Solar Eclipse Photography")
st.header("🕒 Éditeur de script d'ordonnancement")

# SECTION 1: Nettoyage du formulaire
if st.button("🧹 Vider le formulaire"):
    logging.info("ACTION: Formulaire réinitialisé par l'utilisateur.")
    # On remet les valeurs par défaut dans le session_state
    st.session_state["lieu"] = DEFAULT_TOWN
    st.session_state["date_saisie"] = DEFAULT_DATE
    for p in ["C1", "C2", "Max", "C3", "C4"]:
        st.session_state[f"{p}_h"] = 8
        st.session_state[f"{p}_m"] = 0
        st.session_state[f"{p}_s"] = 0
    st.rerun()

st.subheader("📁 Destination & Import")

# Création de la liste déroulante pour les dossiers favoris
nom_selectionne = st.selectbox(
    "Choisir le dossier :",
    options=list(DOSSIERS_FAVORIS.keys())
)

if nom_selectionne == "➕ Autre...":
    chemin_final = st.text_input(
        "Saisissez le chemin complet du dossier :",
        placeholder="/home/user/mon_dossier/ ou ./mon_dossier/", 
        key="chemin_manuel"
    )
else:
    chemin_final = DOSSIERS_FAVORIS[nom_selectionne]

if chemin_final and os.path.isdir(chemin_final):
    # Option de relecture : lister les fichiers .txt du dossier
    fichiers = [f for f in os.listdir(chemin_final) if f.endswith(".txt")]
    if fichiers:
        fichier_a_ouvrir = st.selectbox("📝 Modifier un fichier existant ?", ["-- Aucun --"] + fichiers)
        if fichier_a_ouvrir != "-- Aucun --":
            if st.button("Charger les données"):
                try:
                    charger_fichier_existant(os.path.join(chemin_final, fichier_a_ouvrir), fichier_a_ouvrir)
                    logging.info(f"SUCCÈS: Fichier chargé : {fichier_a_ouvrir} depuis {chemin_final}")
                except Exception as e:
                    st.error(f"Erreur lors du chargement du fichier : {e}")
                    logging.error(f"ERREUR: Impossible de charger le fichier : {e}")
else:
    if nom_selectionne == "➕ Autre..." and chemin_final:
        st.error("Dossier introuvable.")
        logging.warning(f"AVERTISSEMENT: Chemin manuel introuvable : {chemin_final}")
        st.button("Réinitialiser", on_click=vider_chemin)
    st.stop()

# --- 5. INTERFACE : FORMULAIRE ---
st.divider()
st.success(f"👍 Répertoire de destination : `{os.path.abspath(chemin_final)}`")

col_lieu, col_date = st.columns(2)
with col_lieu:
    # On lie le texte au session_state
    lieu = st.text_input("Lieu :", key="lieu") 
with col_date:
    # On lie la date au session_state
    date_saisie = st.date_input("Date :", key="date_saisie")

st.write("---")

# 1. On affiche C1 (utilise les valeurs initiales du session_state)
c1 = saisie_heure_dynamique("C1")

# 2. Avant d'afficher C2, on vérifie si C2 est à la traîne par rapport à C1
if st.session_state["C2_h"] < c1.hour:
    st.session_state["C2_h"] = c1.hour
    st.session_state["C2_m"] = c1.minute
    st.session_state["C2_s"] = c1.second
c2 = saisie_heure_dynamique("C2")

# 3. Pareil pour Max par rapport à C2
if st.session_state["Max_h"] < c2.hour:
    st.session_state["Max_h"] = c2.hour
    st.session_state["Max_m"] = c2.minute
    st.session_state["Max_s"] = c2.second
max_h = saisie_heure_dynamique("Max")

# 4. C3 doit suivre Max
if st.session_state["C3_h"] < max_h.hour:
    st.session_state["C3_h"] = max_h.hour
    st.session_state["C3_m"] = max_h.minute
    st.session_state["C3_s"] = max_h.second
c3 = saisie_heure_dynamique("C3")

# 5. C4 doit suivre C3
if st.session_state["C4_h"] < c3.hour:
    st.session_state["C4_h"] = c3.hour
    st.session_state["C4_m"] = c3.minute
    st.session_state["C4_s"] = c3.second
c4 = saisie_heure_dynamique("C4")

# --- 6. INTERFACE : TIME LINE ---
st.subheader("📊 Timeline des étapes")

# 1. Préparation des données
noms = ["C1", "C2", "Max", "C3", "C4"]
valeurs = [c1, c2, max_h, c3, c4]
today = datetime.today().date()

# Conversion en objets datetime pour l'axe X
heures_dt = [datetime.combine(today, t) for t in valeurs]

# 2. Création de la figure
fig = go.Figure()

# Ajout de la ligne de base (grise et fine)
fig.add_trace(go.Scatter(
    x=[heures_dt[0], heures_dt[-1]],
    y=[0, 0],
    mode="lines",
    line=dict(color="lightgray", width=2),
    hoverinfo="skip"
))

# Ajout des points (étapes)
fig.add_trace(go.Scatter(
    x=heures_dt,
    y=[0] * 5,
    mode="markers+text",
    marker=dict(
        symbol="line-ns-open", # Symbole de trait vertical |
        size=20,
        line=dict(width=3, color="royalblue")
    ),
    text=noms,
    textposition="top center",
    hovertemplate="<b>%{text}</b><br>Heure: %{x|%H:%M:%S}<extra></extra>"
) )

# 3. Mise en forme de l'affichage
fig.update_layout(
    height=150,
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=False,
    xaxis=dict(
        type='date',
        tickformat='%H:%M:%S',
        showgrid=True,
        gridcolor='whitesmoke',
        range=[
            datetime.combine(today, time(valeurs[0].hour-1, 0)), 
            datetime.combine(today, time(valeurs[-1].hour+1, 0))
        ] # Ajoute une marge d'une heure avant/après
    ),
    yaxis=dict(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        range=[-1, 1] # Centre la ligne verticalement
    ),
    plot_bgcolor="white"
)

# 4. Affichage
st.plotly_chart(fig, use_container_width=True)

# --- 7. INTERFACE : DURÉE DES INTERVALLES ---
st.subheader("🔎 Vérification des Circonstances locales de l'éclipse")

# 2. Création des colonnes pour l'affichage
col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.metric(label="C1 ⮕ C2", value=calculer_duree(c1, c2))
with col_d2:
    st.metric(label="C2 ⮕ C3", value=calculer_duree(c2, c3))
with col_d3:
    st.metric(label="C3 ⮕ C4", value=calculer_duree(c3, c4))

# Durée de la totalité (C2 à C3)
duree_totalite = calculer_duree(c2, c3)
st.info(f"**Durée de la totalité (C2 à C3) :** {duree_totalite}")

# Durée totale de l'éclipse (C1 à C4)
duree_totale = calculer_duree(c1, c4)
st.info(f"**Durée de l'éclipse (C1 à C4) :** {duree_totale}")

# --- 8. ENREGISTREMENT ---
if st.button("💾 Enregistrer les modifications"):
    heures = [c1, c2, max_h, c3, c4]
    if all(heures[i] < heures[i+1] for i in range(len(heures)-1)):
        contenu = f"{DEFAULT_ACTION_CONFIG}" + ",".join([h.strftime("%H:%M:%S") for h in heures])
        nom_fichier = f"{lieu}-{date_saisie.strftime('%d_%m_%Y')}.txt"
        chemin_complet = os.path.join(chemin_final, nom_fichier)
        # Avant d'écraser un fichier existant, on en fait une copie de sécurité
        if copier_fichier_securite(chemin_complet) == "Erreur lors de la copie de sécurité":
            st.error("L'enregistrement a été annulé en raison d'une erreur lors de la création de la copie de sécurité.")
            st.stop()
        # Ensuite, on écrit le nouveau contenu
        if os.path.isfile(chemin_complet):
            if conserver_lignes_existantes(chemin_complet, "Config,", contenu) == "Lignes conservées et mises à jour":
                logging.info(f"SUCCÈS: Lignes existantes conservées et mises à jour dans : {chemin_complet}")
                st.success(f"✅ Mise à jour de : `{nom_fichier}`")
            else:
                logging.error(f"ERREUR: Impossible de conserver les lignes existantes dans : {chemin_complet}")
                st.error("L'enregistrement a été annulé en raison d'une erreur lors de la conservation des lignes existantes.")
                st.stop()
        else:
            if ecrire_nouveau_fichier(chemin_complet, contenu) == "Fichier créé":
                logging.info(f"SUCCÈS: Création du fichier : {nom_fichier} dans {chemin_final}")
                st.success(f"✅ Enregistré : `{nom_fichier}`")
                #st.balloons()
            else:
                logging.error(f"ERREUR: Impossible d'écrire dans le fichier : {chemin_complet}")
                st.error("⚠️ Une erreur est survenue lors de l'enregistrement du fichier.")
    else:
        st.error("⚠️ La chronologie n'est pas respectée (C1 < C2 < Max < C3 < C4) !")