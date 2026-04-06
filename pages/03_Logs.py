import streamlit as st
import os

st.set_page_config(page_title="Logs Système", page_icon="📜")

st.title("📜 Journaux d'activité")
st.info("Cette page affiche les derniers événements enregistrés par l'application.")

log_file = "app_activity.log"

# --- LOGIQUE DE LECTURE ---
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
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
    if st.button("🗑️ Effacer les logs"):
        with open(log_file, "w") as f:
            f.write("")
        st.rerun()
else:
    st.write("Aucun fichier de log trouvé. Les actions n'ont pas encore été enregistrées.")

# --- BOUTON DE TÉLÉCHARGEMENT ---
if os.path.exists(log_file):
    with open(log_file, "rb") as file:
        st.download_button(
            label="📥 Télécharger le fichier log complet",
            data=file,
            file_name="mon_hub_logs.log",
            mime="text/plain"
        )