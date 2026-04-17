#!/usr/bin/env python3
"""
Programme de contrôle d'un GeminiAutoFlatPanel via USB/Serial pour régler la position Opened et Closed du filtre.
Il utilise la classe `GeminiAutoFlatPanel` définie dans `filter_controller.py`.
"""

import streamlit as st
import logging
from datetime import datetime
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

# Variable pour suivre l'état de l'étape 1
if 'closed_position_set' not in st.session_state:
    st.session_state.closed_position_set = False

def get_telemetry(deviceId, motorStatus, lightStatus, coverStatus):
    motor_labels = {
        0: "STOPPED ✅",
        1: "RUNNING ⚙️"
    }
    cover_labels = {
        0: "TRANSITION - MOVING ⚠️",
        1: "SAFE - FILTER ENGAGED ✅",
        2: "DANGER - FILTER RETRACTED 🔥",
        3: "ERROR - UNKNOWN POSITION ❌"
    }
    return {
        "device_id": f"UNIT_{deviceId}" if deviceId is not None else "UNKNOWN_DEVICE ❓",
        "motor": motor_labels.get(motorStatus, "UNKNOWN ❓"),
        "light": "ON 💡" if lightStatus == 1 else "OFF 🌑",
        "status": cover_labels.get(coverStatus, "CRITICAL ERROR 🚨")
    }

def set_angle(Key):
    angles = [-45, -30, -10, -5, -1, 0, 1, 5, 10, 30, 45]
    angle = st.select_slider("Angle de déplacement du filtre (en degrés)", options=angles, value=0, key="sl"+Key)
    st.info("Utilisez le slider pour sélectionner l'angle de déplacement du filtre. Négatif ➖ pour fermer, Positif ➕ pour ouvrir.")
    st.write(f"Angle sélectionné : {angle}°")
    if st.button("🔀 Déplacer le filtre de l'angle sélectionné", key="bu"+Key):
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
    return angle

def get_setting_position(position_setting, position_status):
    setting_labels = {
        0: "No ⚠️",
        1: "Ok ✅"
    }
    return {
        "position_setting": setting_labels.get(position_setting, "UNKNOWN ❓"),
        "position_status": position_status
    }

def display_status_panel():
    try:
        if panel.connect():
            try:
                if panel.health_check() is not None:
                    logging.info("Health check passed: Le panneau est en bonne santé.")
                    st.toast("Connexion au panneau réussie", icon="✅", duration=1)
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
    if panel.connect():
        # Etape 1 - Closed
        st.divider()
        st.subheader("Etape 1️⃣ Fixer la position fermée [Closed]")
        angle = set_angle("closed")
        if st.button("📐 Valider la position actuelle comme CLOSED"):
            logging.info(f"ACTION: Valider la position comme CLOSED.")
            try:
                result = panel.set_closed_position()
                if result == True:
                    st.toast(f"Position CLOSED validée avec succès", icon="✅", duration="short")
                    logging.info(f"Position CLOSED validée avec succès.")
                    st.session_state.closed_position_set = True
                else:
                    st.error("❌ Échec du réglage de la position CLOSED")
                    logging.error("Échec du réglage de la position CLOSED.")
                    st.session_state.closed_position_set = False
            except Exception as e:
                st.error(f"❌ Une erreur est survenue lors du réglage de la position CLOSED: {e}")
                logging.error(f"Une erreur est survenue lors du réglage de la position CLOSED: {e}")
                st.session_state.closed_position_set = False

        # Etape 2 - Opened
        st.divider()
        st.subheader("Etape 2️⃣ Fixer la position ouverte [Opened]")
        if st.session_state.closed_position_set:
            angle = set_angle("opened")
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
        else:
            st.warning("L'étape 2 n'est pas disponible tant que l'étape 1 n'est pas validée.")

        # Etape 3 - Control
        st.divider()
        st.subheader("Etape 3️⃣ Vérifier que le réglage est effectif")
        if st.button("✅ Vérifier le status du réglage"):
            logging.info(f"ACTION: Vérification du status de réglage des positions.")
            try:
                status = panel.get_angle_set()
                if status:
                    st.toast("Status du setting reçu: ", icon="📶", duration="short")
                    logging.info(f"Setting position status retrieved: {status}")
                telemetry = get_setting_position(
                    position_setting=int(status['position_setting']),
                    position_status=str(status['position_status'])
                )
                if status:
                    col_drive, col_cover = st.columns(2)
                    with col_drive:
                        st.metric(label="Setting", value=telemetry['position_setting'])
                else:
                    st.error("❌ Impossible de lire l'état")
                    logging.error("Impossible de lire l'état du device.")
            except Exception as e:
                st.error(f"❌ Une erreur est survenue lors de la lecture du status: {e}")
                logging.error(f"Une erreur est survenue lors de la lecture du status: {e}")
            finally:
                st.session_state.closed_position_set = False

finally:
    panel.disconnect()
    logging.info("Déconnexion du panneau effectuée.")