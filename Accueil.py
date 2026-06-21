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
        proc = psutil.Process(pid)
        expected_ct = st.session_state.get("sep_create_time")
        if expected_ct is not None and proc.create_time() != expected_ct:
            return False
        return proc.is_running()
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
            script_file = os.path.expandvars(os.path.expanduser(sep_params.get("script_file", "")))

            # Valider que script_file est bien sous $HOME (protection contre les path traversal)
            home_dir = os.path.realpath(os.path.expandvars("$HOME"))
            real_script = os.path.realpath(script_file)
            if (
                not os.path.commonpath([real_script, home_dir]) == home_dir
                or not os.path.isfile(real_script)
            ):
                st.error(f"Chemin script_file invalide ou introuvable : {script_file}")
            else:
                # Déduire le répertoire de travail depuis sep_dir (params) ou le répertoire de sep_params.json
                raw_sep_dir = sep_params.get("sep_dir", os.path.dirname(SEP_PARAMS_PATH))
                sep_dir = os.path.realpath(os.path.expandvars(os.path.expanduser(raw_sep_dir)))

                # Valider que sep_dir est sous $HOME
                if os.path.commonpath([sep_dir, home_dir]) != home_dir or not os.path.isdir(sep_dir):
                    st.error(f"Répertoire sep_dir invalide ou introuvable : {sep_dir}")
                else:
                    main_py = os.path.join(sep_dir, "main.py")
                    cmd = ["python3", main_py, real_script]

                    if sep_params.get("test_mode") is True:
                        cmd.append("--test-mode")

                    log_level = sep_params.get("log_level")
                    if log_level:
                        cmd.extend(["--log-level", str(log_level)])

                    sep_log_path = os.path.join(sep_dir, "sep_process.log")
                    try:
                        with open(sep_log_path, "a") as log_fh:
                            proc = subprocess.Popen(
                                cmd,
                                cwd=sep_dir,
                                stdout=log_fh,
                                stderr=log_fh,
                            )
                        try:
                            create_time = psutil.Process(proc.pid).create_time()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            create_time = None
                        st.session_state["sep_pid"] = proc.pid
                        st.session_state["sep_create_time"] = create_time
                        st.success(f"SEP lancé avec le PID {proc.pid}. Logs : {sep_log_path}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur au lancement de SEP : {e}")
