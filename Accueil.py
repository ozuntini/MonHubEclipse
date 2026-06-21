import streamlit as st
import os
import json
import subprocess
import psutil

# Configuration de la page
st.set_page_config(page_title="Mon Hub Eclipse", layout="centered", page_icon="😎")

st.title("😎 Hub Eclipse 😎")
st.write("""
Cette interface regroupe tous mes outils Python d'observation des éclipses Solaires ou Lunaires.  
Utilisez la **barre latérale à gauche** pour naviguer entre les différentes applications.
""")

st.info("Le menu à gauche est généré automatiquement à partir du dossier 'pages/'.")

# ── Section Solar Eclipse Photography (SEP) ──────────────────────────────────

st.divider()
st.subheader("🌑 Solar Eclipse Photography (SEP)")

SEP_PARAMS_PATH = os.path.expandvars("$HOME/Eclipse_Project/sep_params.json")

# Lecture du fichier de paramètres
sep_params = None
if os.path.isfile(SEP_PARAMS_PATH):
    try:
        with open(SEP_PARAMS_PATH, "r") as f:
            sep_params = json.load(f)
        with st.expander("📄 Paramètres SEP", expanded=False):
            st.json(sep_params)
    except Exception as e:
        st.error(f"Erreur lors de la lecture de sep_params.json : {e}")
else:
    st.error(f"Fichier introuvable : {SEP_PARAMS_PATH}")

# Indicateur d'état du processus SEP
if "sep_pid" not in st.session_state:
    st.session_state["sep_pid"] = None

def _is_sep_running():
    pid = st.session_state.get("sep_pid")
    if pid is None:
        return False
    try:
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

sep_running = _is_sep_running()

if sep_running:
    st.success(f"🟢 SEP en cours d'exécution (PID {st.session_state['sep_pid']})")
else:
    st.error("🔴 SEP arrêté")

# Bouton de lancement (affiché uniquement si SEP n'est pas en cours)
if not sep_running:
    if st.button("🚀 Lancer Solar Eclipse Photography"):
        if sep_params is None:
            st.error("Impossible de lancer SEP : fichier de paramètres manquant ou invalide.")
        else:
            # Résoudre les chemins et construire la commande
            script_file = os.path.expandvars(sep_params.get("script_file", ""))
            cmd = ["python3", "main.py", script_file]

            if sep_params.get("test_mode") is True:
                cmd.append("--test-mode")

            log_level = sep_params.get("log_level")
            if log_level:
                cmd.extend(["--log-level", str(log_level)])

            try:
                proc = subprocess.Popen(cmd)
                st.session_state["sep_pid"] = proc.pid
                st.success(f"SEP lancé avec le PID {proc.pid}.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur au lancement de SEP : {e}")
