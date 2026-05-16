from datetime import datetime

import streamlit as st
import os
import shutil

st.set_page_config(page_title="Logs Système", page_icon="📜")

st.title("📜 Journaux d'activité")
st.info("Cette page affiche les derniers événements enregistrés par l'application.")

DOSSIERS_LOG = os.path.expanduser("~/Eclipse_Project/logs")
if not os.path.exists(DOSSIERS_LOG):
    os.makedirs(DOSSIERS_LOG)

read_log_file = os.path.join(DOSSIERS_LOG, "horaires.log")

if DOSSIERS_LOG and os.path.isdir(DOSSIERS_LOG):
    # Option de relecture : lister les fichiers .log du dossier
    fichiers = [f for f in os.listdir(DOSSIERS_LOG) if f.endswith(".log")]
    if fichiers:
        fichier_a_ouvrir = st.selectbox("🔎 Ouvrir un fichier de log ?", fichiers, index=0)
        read_log_file = os.path.join(DOSSIERS_LOG, fichier_a_ouvrir)
    else:
        st.warning("Aucun fichier de log trouvé dans le dossier.", icon="⚠️")

# --- LOGIQUE DE LECTURE ---
if os.path.exists(read_log_file):
    with open(read_log_file, "r", encoding="utf-8") as f:
        # On lit les lignes et on les inverse pour avoir les plus récentes en haut
        logs = f.readlines()
        logs.reverse() 

    # --- FILTRES ---
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 Rechercher un mot-clé (ex: ERROR, Paris...)")
    with col2:
        nb_lignes = st.slider("Nombre de lignes à afficher", 5, 100, 20)

    # --- AFFICHAGE ---
    st.divider()
    
    # Filtrage simple
    logs_filtres = [line for line in logs if search.lower() in line.lower()]
    
    if logs_filtres:
        # On affiche les logs dans un bloc de code pour garder le formatage
        contenu_logs = "".join(logs_filtres[:nb_lignes])
        st.code(contenu_logs, language="text")
    else:
        st.warning("Aucun log ne correspond à votre recherche.")

    # --- ACTIONS ---
    if st.button("🔁 Rotation des logs"):
        # On renomme et on décale les fichiers de log actuel pour créer une archive
        if read_log_file and os.path.exists(read_log_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{read_log_file}.{timestamp}"
            os.rename(read_log_file, rotated_name)
        with open(read_log_file, "w") as f:
            f.write("") # On vide le fichier de log actuel
        st.success("Rotation des logs effectuée. Les anciens logs sont sauvegardés.")
        st.rerun()

    # --- ACTIONS ---
    if st.button("🗑️ Effacer les logs"):
        with open(read_log_file, "w") as f:
            f.write("")
        st.success("Les logs ont été effacés.")
        st.rerun()
else:
    st.write("Aucun fichier de log trouvé. Les actions n'ont pas encore été enregistrées.")

# --- BOUTON DE TÉLÉCHARGEMENT ---
if os.path.exists(read_log_file):
    with open(read_log_file, "rb") as file:
        st.download_button(
            label="📥 Télécharger le fichier log complet",
            data=file,
            file_name="mon_hub_logs.log",
            mime="text/plain"
        )