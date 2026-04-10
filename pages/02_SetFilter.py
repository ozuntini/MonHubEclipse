#!/usr/bin/env python3
"""
Programme de contrôle d'un GeminiAutoFlatPanel via USB/Serial pour régler la position Opened et Closed du filtre.
Il utilise la classe `GeminiAutoFlatPanel` définie dans `filter_controller.py`.
"""

import streamlit as st
import logging
from hardware.filter_controller import GeminiAutoFlatPanel, CoverState

# Configuration du logger
log_file = "app_activity.log"
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

# Créer une instance
panel = GeminiAutoFlatPanel(port=port, baudrate=baudrate, timeout=timeout)

st.set_page_config(page_title="Set Filter", page_icon="🛠️", layout="wide")

# --- 5. INTERFACE : DESTINATION & LECTURE ---
st.title("😎 Solar Eclipse Photography")
st.header("🛠️ Réglage de la position du filtre")

try:
    # Se connecter
    if panel.connect():
        try:
            if panel.health_check() is not None:
                logging.info("Health check passed: Le panneau est en bonne santé.")
                st.success("✅ Connexion réussie au panneau GeminiAutoFlatPanel")
                status = panel.get_device_status()
                logging.info(f"Device status retrieved: {status}")
                telemetry = get_telemetry(
                    deviceId=str(status['device_id']),
                    motorStatus=int(status['motor_status']),
                    lightStatus=int(status['light_status']),
                    coverStatus=int(status['cover_status'])
                )
                if status:
                    st.success("➡️ État du device: ")
                    col_id, col_drive, col_cover = st.columns(3)
                    with col_id:
                        st.metric(label="Device ID", value=telemetry['device_id'])
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

    col_open, col_close = st.columns(2)
    with col_open:
        if st.button("⤴️ Ouvrir le filtre"):
            logging.info("ACTION: Ouvrir le filtre demandé.")
            try:
                result = panel.open_cover()
                if result == CoverState.OPENED:
                    st.success("✅ Filtre ouvert avec succès")
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
                    st.success("✅ Filtre fermé avec succès")
                    logging.info("Filtre fermé avec succès.")
                else:
                    st.error("❌ Échec de la fermeture du filtre")
                    logging.error("Échec de la fermeture du filtre.")
            except Exception as e:
                st.error(f"❌ Une erreur est survenue lors de la fermeture du filtre: {e}")
                logging.error(f"Une erreur est survenue lors de la fermeture du filtre: {e}")

finally:
    # Toujours fermer la connexion
    panel.disconnect()
    logging.info("Déconnexion du panneau effectuée.")