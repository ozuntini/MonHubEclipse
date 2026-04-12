#!/usr/bin/env python3
"""
Programme de contrôle d'un GeminiAutoFlatPanel via USB/Serial pour régler la position Opened et Closed du filtre.
Il utilise la classe `GeminiAutoFlatPanel` définie dans `filter_controller.py`.
"""

import streamlit as st
import logging
from datetime import datetime
# On part du nom du DOSSIER, puis du nom du FICHIER (sans .py)
from filter_control.filter_controller import GeminiAutoFlatPanel, CoverState

# Configuration du logger
log_file = "/home/ozuntini/log/app_activity.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

port = '/dev/gflatpanel'  # Port par défaut, à ajuster selon votre système
baudrate = 9600
timeout = 1


def get_telemetry(deviceId, motorStatus, lightStatus, coverStatus):
    # Mapping pour le moteur
    # 0: Arrêté, 1: En mouvement
    motor_labels = {
        0: "STOPPED ✅",
        1: "RUNNING ⚙️"
    }

    # Mapping critique pour le couvercle (Filtre Solaire)
    # On utilise des termes de sécurité pour éviter toute confusion
    cover_labels = {
        0: "TRANSITION - MOVING ⚠️",      # En cours de mouvement
        1: "SAFE - FILTER ENGAGED ✅",    # Filtre bien en place
        2: "DANGER - FILTER RETRACTED 🔥", # Filtre retiré (Photo uniquement)
        3: "ERROR - UNKNOWN POSITION ❌"   # État indéterminé
    }

    return {
        "device_id": f"UNIT_{deviceId}" if deviceId is not None else "UNKNOWN_DEVICE ❓",
        "motor": motor_labels.get(motorStatus, "UNKNOWN ❓"),
        "light": "ON 💡" if lightStatus == 1 else "OFF 🌑",
        "status": cover_labels.get(coverStatus, "CRITICAL ERROR 🚨")
    }

def display_status_panel():
    try:
        # Se connecter
        if panel.connect():
            try:
                if panel.health_check() is not None:
                    logging.info("Health check passed: Le panneau est en bonne santé.")
                    st.toast("Connexion au panneau réussie", icon="✅", duration="short")
                    status = panel.get_device_status()
                    logging.info(f"Device status retrieved: {status}")
                    telemetry = get_telemetry(
                        deviceId=str(status['device_id']),
                        motorStatus=int(status['motor_status']),
                        lightStatus=int(status['light_status']),
                        coverStatus=int(status['cover_status'])
                    )
                    if status:
                        col_drive, col_cover = st.columns(2)
                        with col_drive:
                            st.metric(label="Motor Status", value=telemetry['motor'])
                        with col_cover:
                            st.metric(label="Cover Status", value=telemetry['status'])
                    else:
                        st.error("❌ Impossible de lire l'état")
            except Exception as e:
                logging.error(f"Une erreur est survenue lors de l'exécution de l'action: {e}")
        else:
            st.error("❌ Échec de la connexion au panneau")
    finally:
        # Toujours fermer la connexion
        panel.disconnect()
        logging.info("Déconnexion du panneau effectuée.")

# Créer une instance
panel = GeminiAutoFlatPanel(port=port, baudrate=baudrate, timeout=timeout)

st.set_page_config(page_title="Set Filter", page_icon="🛠️", layout="wide")

# --- 1. INTERFACE : Générale ---
st.title("😎 Solar Eclipse Photography")

# --- 2. INTERFACE : Status et mouvement ---
st.divider()
st.header(" 🔎 Etat du filtre")

try:
    # Se connecter
    if panel.connect():
        col_status, col_open, col_close = st.columns(3)
        with col_status:
            if st.button("🔄 Status du filtre"):
                logging.info("ACTION: Lecture du status du filtre demandé.")
                try:
                    status = panel.get_device_status()
                    logging.info(f"Device status retrieved: {status}")
                    if status:
                        st.toast("Status du device reçu: ", icon="📶", duration="short")
                    else:
                        st.error("❌ Impossible de lire l'état")
                        logging.error("Impossible de lire l'état du device.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors de la lecture du status: {e}")
                    logging.error(f"Une erreur est survenue lors de la lecture du status: {e}")

        with col_open:
            if st.button("⤴️ Ouvrir le filtre"):
                logging.info("ACTION: Ouvrir le filtre demandé.")
                try:
                    result = panel.open_cover()
                    if result == CoverState.OPENED:
                        st.toast("Filtre ouvert avec succès", icon="✅", duration="short")
                        logging.info("Filtre ouvert avec succès.")
                    else:
                        st.error("❌ Échec de l'ouverture du filtre")
                        logging.error("Échec de l'ouverture du filtre.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors de l'ouverture du filtre: {e}")
                    logging.error(f"Une erreur est survenue lors de l'ouverture du filtre: {e}")

        with col_close:
            if st.button("⤵️ Fermer le filtre"):
                logging.info("ACTION: Fermer le filtre demandé.")
                try:
                    result = panel.close_cover()
                    if result == CoverState.CLOSED:
                        st.toast("Filtre fermé avec succès", icon="✅", duration="short")
                        logging.info("Filtre fermé avec succès.")
                    else:
                        st.error("❌ Échec de la fermeture du filtre")
                        logging.error("Échec de la fermeture du filtre.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors de la fermeture du filtre: {e}")
                    logging.error(f"Une erreur est survenue lors de la fermeture du filtre: {e}")
finally:
    display_status_panel()

# --- 2. INTERFACE : Status et mouvement ---
st.divider()
st.header("🛠️ Interface de réglages")
    
try:
    # Se connecter
    if panel.connect():
        st.warning("Attention ! ne pas utiliser les commandes Ouverture et Fermeture ci-dessus pendant le réglage", icon="⚠️")
        # On détermine l'angle de déplacement avec la fonction slider
        angles = [-45, -10, -1, 0, 1, 10, 45]
        angle = st.select_slider("Angle de déplacement du filtre (en degrés)", options=angles, value=0)
        st.info("Utilisez le slider pour sélectionner l'angle de déplacement du filtre. Négatif ➖ pour fermer, Positif ➕ pour ouvrir.")
        st.write(f"Angle sélectionné : {angle}°")
        col_move_to, col_set_open, col_set_close = st.columns(3)
        with col_move_to:
            if st.button("🔀 Déplacer le filtre de l'angle sélectionné"):
                logging.info(f"ACTION: Déplacer le filtre de l'angle {angle}° demandé.")
                try:
                    result = panel.move_to_position(angle)
                    if result == True:
                        st.toast(f"Filtre déplacé à {angle}° avec succès", icon="✅", duration="short")
                        logging.info(f"Filtre déplacé à {angle}° avec succès.")
                    else:
                        st.error("❌ Échec du déplacement du filtre")
                        logging.error("Échec du déplacement du filtre.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors du déplacement du filtre: {e}")
                    logging.error(f"Une erreur est survenue lors du déplacement du filtre: {e}")

        with col_set_open:
            if st.button("📐 Valider la position actuelle comme OPENED"):
                logging.info(f"ACTION: Valider la position comme OPENED.")
                try:
                    result = panel.set_open_position()
                    if result == True:
                        st.toast(f"Position OPENED validée avec succès", icon="✅", duration="short")
                        logging.info(f"Position OPENED validée avec succès.")
                    else:
                        st.error("❌ Échec du réglage de la position OPENED")
                        logging.error("Échec du réglage de la position OPENED.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors du réglage de la position OPENED: {e}")
                    logging.error(f"Une erreur est survenue lors du réglage de la position OPENED: {e}")
        with col_set_close:
            if st.button("📐 Valider la position actuelle comme CLOSED"):
                logging.info(f"ACTION: Valider la position comme CLOSED.")
                try:
                    result = panel.set_closed_position()
                    if result == True:
                        st.toast(f"Position CLOSED validée avec succès", icon="✅", duration="short")
                        logging.info(f"Position CLOSED validée avec succès.")
                    else:
                        st.error("❌ Échec du réglage de la position CLOSED")
                        logging.error("Échec du réglage de la position CLOSED.")
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue lors du réglage de la position CLOSED: {e}")
                    logging.error(f"Une erreur est survenue lors du réglage de la position CLOSED: {e}")
finally:
    # Toujours fermer la connexion
    panel.disconnect()
    logging.info("Déconnexion du panneau effectuée.")