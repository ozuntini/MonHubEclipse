#!/usr/bin/env python3
"""
Programme de vérification de la configuration avant lancement de la séquence d'Eclipse
- Affiche le nom du boitier : cameramodel
- Affiche l'date et heure du boitier : datetime - vérifier la différence avec l'heur du PC
- affiche le niveau de batterie : batterylevel - alerte si < à 95%
- affiche la durée du autopoweroff : autpoweroff - alerte si < à 5 minutes si 0 ok
- affiche le mode : autoexposuremode - OK si Manual alerte si autre
- affiche le type de fichier : imageformat - OK si raw alerte si autre
- Affiche le Focus Mode : focusmode - OK si Manual alerte si autre
- Affiche le Drive Mode : drivemode - OK si Single alerte si autre
- Si le modele est 6D Affiche le reviewtime- Ok si 0 alerte si autre
Vérification à faire manuellement :
- Vérifier que la carte SD est bien vidée et formatée
- Si le modele est R6 Review Image doit être à 0
"""

import streamlit as st
import gphoto2 as gp
from datetime import datetime
import logging

# Configuration du logger
log_file = "/home/ozuntini/log/app_activity.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Fonction pour initialiser la caméra et le contexte
def initialize_camera():
    context = gp.gp_context_new()
    camera = gp.check_result(gp.gp_camera_new())
    try:
        gp.check_result(gp.gp_camera_init(camera, context))
        logging.info("Camera initialized successfully.")
        return camera, context
    except gp.GPhoto2Error:
        logging.error("No camera found.")
        return None, None

# Fonction pour fermer la connexion à la caméra
def close_camera(camera, context):
    gp.gp_camera_exit(camera, context)
    logging.info("Camera connection closed.")

# Fonction pour récupérer le modèle de la caméra
def get_camera_model(camera, context):
    try:
        config = gp.check_result(gp.gp_camera_get_config(camera, context))
        model_widget = gp.check_result(gp.gp_widget_get_child_by_name(config, "cameramodel"))
        logging.info("Camera model retrieved successfully.")
        return gp.check_result(gp.gp_widget_get_value(model_widget))
    except gp.GPhoto2Error:
        logging.error("Failed to get camera model.")
        return "Unknown Model"
    
# Fonction pour récupérer un paramètre par son nom
def get_param_by_name(camera, name, context):
    try:
        config = gp.check_result(gp.gp_camera_get_config(camera, context))
        widget = gp.check_result(gp.gp_widget_get_child_by_name(config, name))
        logging.info(f"Parameter '{name}' retrieved successfully.")
        return widget
    except gp.GPhoto2Error:
        logging.error(f"Failed to get parameter: {name}")  
        return None

# Configuration de la page Streamlit
st.set_page_config(page_title="Set Config", page_icon="📷", layout="wide")

# Titre de la page
st.title(f"Vérification de la configuration du boitier")
if st.button("🔄 Recharger la page pour refaire les vérifications"):
    st.rerun()

# Initialisation de la caméra
camera, context = initialize_camera()
if not camera:
    st.error(" ⚠️ Aucune caméra détectée. Veuillez connecter une caméra et réessayer.")
    st.stop()

model = get_camera_model(camera, context)


# Sous-titre pour les vérifications automatiques
st.subheader(f"📷 Vérifications automatiques du {model}")

# Liste des paramètres à vérifier avec leurs conditions d'alerte
params_to_check = [
    ("datetime", "Date et heure du boitier"),
    ("batterylevel", "Niveau de batterie", ">", 95),
    ("autopoweroff", "Durée du autopoweroff", ">", 60),
    ("autoexposuremode", "Mode d'exposition automatique", "==", "Manual"),
    ("imageformat", "Type de fichier", "==", "RAW"),
    ("focusmode", "Mode de mise au point", "==", "Manual"),
    ("drivemode", "Mode de prise de vue", "==", "Single"),
]

EOS6D_specific_check = ("reviewtime", "Review Time", "==", "None")
EOSR6_specific_check = ()

# Vérification de chaque paramètre et affichage des résultats
for param_name, display_name, *check in params_to_check:
    widget = get_param_by_name(camera, param_name, context)
    if widget is not None:
        if param_name == "datetime":
            camera_time_seconds = gp.check_result(gp.gp_widget_get_value(widget))
            camera_time = datetime.fromtimestamp(camera_time_seconds)
            pc_time = datetime.now()
            time_diff = abs((camera_time - pc_time).total_seconds())
            if time_diff > 1:
                st.warning(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes) - La différence de temps est supérieure à 1 seconde.", icon="⚠️")
                logging.warning(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)")
                logging.warning("La différence de temps entre la caméra et le PC est supérieure à 1 seconde.")
            else:
                st.success(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)", icon="✅")
                logging.info(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)")
        else:
            value = gp.check_result(gp.gp_widget_get_value(widget))
            logging.info(f"{display_name} : {value}")
            # Add specific checks and alerts based on the parameter
            if check:
                operator, expected_value = check
                if operator == ">" and int(value.strip().rstrip("%")) <= int(expected_value):
                    st.warning(f"{display_name} : {value} doit être supérieur à {expected_value}.", icon="⚠️")
                    logging.warning(f"{display_name} : {value} doit être supérieur à {expected_value}.")
                elif operator == "==" and value != expected_value:
                    st.warning(f"{display_name} : {value} doit être {expected_value}.", icon="⚠️")
                    logging.warning(f"{display_name} : {value} doit être {expected_value}.")
                else:
                    st.success(f"{display_name} : {value}", icon="✅")
            else:
                st.success(f"{display_name} : {value}", icon="✅")

# Vérification spécifique pour le modèle 6D
if "6D" in model:
    for param_name, display_name, *check in [EOS6D_specific_check]:
        widget = get_param_by_name(camera, param_name, context)
        if widget is not None:
            value = gp.check_result(gp.gp_widget_get_value(widget))
            logging.info(f"{display_name} : {value}")
            if check:
                operator, expected_value = check
                if operator == "==" and value != expected_value:
                    st.warning(f"{display_name} : {value} - {display_name} doit être {expected_value} pour le modèle 6D.", icon="⚠️")
                    logging.warning(f"{display_name} : {value} - {display_name} doit être {expected_value} pour le modèle 6D.")
                else:
                    st.success(f"{display_name} : {value}", icon="✅")
            else:
                st.success(f"{display_name} : {value}", icon="✅")

# Sous-titre pour les vérifications manuelles
st.subheader(" 🫵 Vérifications manuelles à effectuer :")

st.write("Vérifier que la carte SD est bien vidée et formatée.")
# Vérification spécifique pour le modèle R6
if "R6" in model:
    st.write("Vérifier que le Review Image est désactivé.")

# Fermer la connexion à la caméra
close_camera(camera, context)
st.divider()
st.success("✅ Vérification de la configuration terminée. Vous pouvez maintenant lancer la séquence d'Eclipse.")
