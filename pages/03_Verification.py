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

# Configuration du journal des checks
check_log_file = "/home/ozuntini/log/checks.log"
check_logger = logging.getLogger("checks_logger")
check_logger.setLevel(logging.INFO)
check_handler = logging.FileHandler(check_log_file)
check_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
check_logger.addHandler(check_handler)

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

# Fonction pour définir un paramètre par son nom
def set_param_by_name(camera, name, value, context):
    try:
        config = gp.check_result(gp.gp_camera_get_config(camera, context))
        widget = gp.check_result(gp.gp_widget_get_child_by_name(config, name))
        gp.check_result(gp.gp_widget_set_value(widget, value))
        gp.check_result(gp.gp_camera_set_config(camera, config, context))
        logging.info(f"Parameter '{name}' set to '{value}' successfully.")
    except gp.GPhoto2Error:
        logging.error(f"Failed to set parameter: {name} to {value}")

# Configuration de la page Streamlit
st.set_page_config(page_title="Set Config", page_icon="📷", layout="wide")

# Titre de la page
st.title("😎 Solar Eclipse Photography")
st.header(f"✅ Vérification de la configuration du boitier")
if st.button("Recharger la page pour refaire les vérifications", icon="🔄", help="Cliquez pour refaire les vérifications"):
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
    ("datetime", "Date et heure du boitier", ">", 2),  # Alerte si la différence de temps est supérieure à 2 secondes (la précision est 1 seconde)
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
            accept_diff_seconds = check[1] if len(check) > 1 else 2  # Utiliser la valeur d'alerte spécifique ou 2 secondes par défaut
            camera_time_seconds = gp.check_result(gp.gp_widget_get_value(widget))
            camera_time = datetime.fromtimestamp(camera_time_seconds)
            pc_time = datetime.now()
            time_diff = abs((camera_time - pc_time).total_seconds())
            if time_diff > accept_diff_seconds:
                st.warning(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes) - La différence de temps est supérieure à {accept_diff_seconds} secondes.", icon="⚠️")
                logging.warning(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)")
                logging.warning(f"La différence de temps entre la caméra et le PC est supérieure à {accept_diff_seconds} secondes.")
                if st.button("Synchroniser la date et l'heure de la caméra avec le PC", icon="⏱️", help="Cliquez pour synchroniser la date et l'heure de la caméra avec celle du PC"):
                    set_param_by_name(camera, "syncdatetimeutc", 1, context)
                    st.success("Date et heure de la caméra synchronisées avec le PC.", icon="✅")
                    logging.info("Date et heure de la caméra synchronisées avec le PC.")
                    st.rerun()
            else:
                st.success(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)", icon="✅")
                logging.info(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes)")
                check_logger.info(f"{display_name} : {camera_time} (Différence avec PC : {time_diff:.2f} secondes) - OK")

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
                    check_logger.info(f"{display_name} : {value} - OK")
            else:
                st.success(f"{display_name} : {value}", icon="✅")
                check_logger.info(f"{display_name} : {value} - OK")

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
                    check_logger.info(f"{display_name} : {value} - OK")
            else:
                st.success(f"{display_name} : {value}", icon="✅")
                check_logger.info(f"{display_name} : {value} - OK")

# Sous-titre pour les vérifications manuelles
st.subheader(" 🫵 Vérifications manuelles à effectuer")

agree = st.checkbox("Vérifier que la carte SD est bien vidée et formatée.", value=False)
if agree:
    check_logger.info("Vérification manuelle : Carte SD vidée et formatée - OK")

# Vérification spécifique pour le modèle R6
if "R6" in model:
    agree = st.checkbox("Vérifier que le Review Image est désactivé.", value=False)
    if agree:
        check_logger.info("Vérification manuelle : Review Image désactivé - OK")

# Fermer la connexion à la caméra
close_camera(camera, context)
st.divider()
st.success("✅ Vérification de la configuration terminée. Vous pouvez maintenant lancer la séquence d'Eclipse.")
