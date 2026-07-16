import streamlit as st
import os
import json
import subprocess
import psutil
import logging

# Configuration du logger
DOSSIER_LOG = os.path.expanduser("~/Eclipse_Project/logs")
if not os.path.exists(DOSSIER_LOG):
    os.makedirs(DOSSIER_LOG)

logger = logging.getLogger("accueil")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(DOSSIER_LOG, "accueil.log"))
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Configuration de la page
st.set_page_config(page_title="Mon Hub Eclipse", layout="centered", page_icon="😎")
logger.info("Page d'accueil chargée.")

st.title("😎 Hub Eclipse 😎")
st.write("""
Cette interface regroupe tous mes outils Python d'observation des éclipses Solaires ou Lunaires.  
Utilisez la **barre latérale à gauche** pour naviguer entre les différentes applications.
""")

#st.info("Le menu à gauche est généré automatiquement à partir du dossier 'pages/'.")

# ── Section Solar Eclipse Photography (SEP) ──────────────────────────────────

st.divider()
st.subheader("🌑 Solar Eclipse Photography (SEP)")

SEP_PARAMS_PATH = os.path.expandvars(
    os.environ.get("SEP_PARAMS_PATH", "$HOME/Eclipse_Project/sep_params.json")
)
logger.info(f"Chemin du fichier de paramètres SEP : {SEP_PARAMS_PATH}")

# Lecture du fichier de paramètres
sep_params = None
if os.path.isfile(SEP_PARAMS_PATH):
    try:
        with open(SEP_PARAMS_PATH, "r") as f:
            sep_params = json.load(f)
            logger.info(f"Fichier de paramètres SEP chargé avec succès : {SEP_PARAMS_PATH}")
        with st.expander("📄 Paramètres SEP", expanded=False):
            st.json(sep_params)
            logger.debug("Affichage des paramètres SEP dans l'expander.")
    except Exception as e:
        st.error(f"Erreur lors de la lecture de sep_params.json : {e}")
        logger.exception("Erreur lors de la lecture de sep_params.json")
else:
    st.error(f"Fichier introuvable : {SEP_PARAMS_PATH}")
    logger.error(f"Fichier introuvable : {SEP_PARAMS_PATH}")

# Indicateur d'état du processus SEP
if "sep_pid" not in st.session_state:
    st.session_state["sep_pid"] = None

def _under_home(path: str, home: str) -> bool:
    """Retourne True si path (résolu) est strictement sous home (résolu) ou égal à home."""
    # home doit se terminer par os.sep pour éviter le faux-positif /home/user vs /home/user2
    home_prefix = home if home.endswith(os.sep) else home + os.sep
    result = path == home or path.startswith(home_prefix)
    logger.debug(f"Vérification du chemin : {path} sous {home} => {result}")
    return result

def _is_sep_running():
    pid = st.session_state.get("sep_pid")
    if pid is None:
        logger.debug("Aucun PID SEP en session_state.")
        return False
    try:
        proc = psutil.Process(pid)
        expected_ct = st.session_state.get("sep_create_time")
        if expected_ct is not None and proc.create_time() != expected_ct:
            logger.warning(
                "PID SEP réutilisé ou create_time différent (pid=%s, attendu=%s, actuel=%s)",
                pid,
                expected_ct,
                proc.create_time(),
            )
            return False
        return proc.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        logger.warning(f"Processus SEP avec PID {pid} non trouvé ou accès refusé.")
        return False
        
sep_running = _is_sep_running()

if sep_running:
    st.success(f"🟢 SEP en cours d'exécution (PID {st.session_state['sep_pid']})")
else:
    st.error("🔴 SEP arrêté")

# Bouton de lancement (affiché uniquement si SEP n'est pas en cours)
if not sep_running:
    if st.button("🚀 Lancer Solar Eclipse Photography"):
        logger.info("Demande utilisateur de lancement SEP.")
        if sep_params is None:
            st.error("Impossible de lancer SEP : fichier de paramètres manquant ou invalide.")
            logger.error("Lancement SEP impossible : paramètres SEP absents ou invalides.")
        else:
            # Résoudre les chemins et construire la commande
            raw_script = sep_params.get("script_file")
            if not raw_script:
                st.error("Paramètre script_file absent ou vide dans sep_params.json.")
                logger.error("Paramètre script_file absent ou vide dans sep_params.json.")
            else:
                script_file = os.path.expandvars(os.path.expanduser(raw_script))

                # Valider que script_file est bien sous $HOME (protection contre les path traversal)
                home_dir = os.path.realpath(os.path.expandvars("$HOME"))
                real_script = os.path.realpath(script_file)
                if not _under_home(real_script, home_dir) or not os.path.isfile(real_script):
                    st.error(f"Chemin script_file invalide ou introuvable : {script_file}")
                    logger.error(
                        "script_file invalide/introuvable (raw=%s, resolved=%s, home=%s)",
                        raw_script,
                        real_script,
                        home_dir,
                    )
                else:
                    # Déduire le répertoire de travail depuis sep_dir (params) ou le répertoire de sep_params.json
                    raw_sep_dir = sep_params.get("sep_dir", os.path.dirname(SEP_PARAMS_PATH))
                    sep_dir = os.path.realpath(os.path.expandvars(os.path.expanduser(raw_sep_dir)))

                    # Valider que sep_dir est sous $HOME
                    if not _under_home(sep_dir, home_dir) or not os.path.isdir(sep_dir):
                        st.error(f"Répertoire sep_dir invalide ou introuvable : {sep_dir}")
                        logger.error(
                            "sep_dir invalide/introuvable (raw=%s, resolved=%s, home=%s)",
                            raw_sep_dir,
                            sep_dir,
                            home_dir,
                        )
                    # Déterminer le chemin vers main.py dans sep_dir
                    raw_main_dir = sep_params.get("main_dir", sep_dir)
                    main_dir = os.path.realpath(os.path.expandvars(os.path.expanduser(raw_main_dir)))
                    if not _under_home(main_dir, home_dir) or not os.path.isdir(main_dir):
                        st.error(f"Répertoire main_dir invalide ou introuvable : {main_dir}")
                        logger.error(
                            "main_dir invalide/introuvable (raw=%s, resolved=%s, home=%s)",
                            raw_main_dir,
                            main_dir,
                            home_dir,
                        )

                    # Déterminer le fichier de log
                    # log_file = log_dir + log_file récupéré depuis sep_params.json ou défaut "sep.log"
                    raw_log_dir = sep_params.get("log_dir", os.path.join(DOSSIER_LOG, "sep"))
                    log_dir = os.path.realpath(os.path.expandvars(os.path.expanduser(raw_log_dir)))
                    if not _under_home(log_dir, home_dir):
                        st.error(f"Répertoire log_dir invalide : {log_dir}")
                        logger.error(
                            "log_dir invalide (raw=%s, resolved=%s, home=%s)",
                            raw_log_dir,
                            log_dir,
                            home_dir,
                        )
                    if not os.path.exists(log_dir):
                        try:
                            os.makedirs(log_dir)
                            logger.info(f"Répertoire de logs créé : {log_dir}")
                        except Exception as e:
                            st.error(f"Impossible de créer le répertoire de logs : {log_dir}. Erreur : {e}")
                            logger.exception(f"Impossible de créer le répertoire de logs : {log_dir}")
                    log_file_name = sep_params.get("log_file", "sep.log")
                    sep_log_file = os.path.join(log_dir, log_file_name)

                    # Déterminer le fichier journal
                    # journal_file = journal_dir + journal_file récupéré depuis sep_params.json ou défaut "sep.journal"
                    raw_journal_dir = sep_params.get("journal_dir", os.path.join(DOSSIER_LOG, "sep"))
                    journal_dir = os.path.realpath(os.path.expandvars(os.path.expanduser(raw_journal_dir)))
                    if not _under_home(journal_dir, home_dir):
                        st.error(f"Répertoire journal_dir invalide : {journal_dir}")
                        logger.error(
                            "journal_dir invalide (raw=%s, resolved=%s, home=%s)",
                            raw_journal_dir,
                            journal_dir,
                            home_dir,
                        )
                    if not os.path.exists(journal_dir):
                        try:
                            os.makedirs(journal_dir)
                            logger.info(f"Répertoire de journal créé : {journal_dir}")
                        except Exception as e:
                            st.error(f"Impossible de créer le répertoire de journal : {journal_dir}. Erreur : {e}")
                            logger.exception(f"Impossible de créer le répertoire de journal : {journal_dir}")
                    journal_file_name = sep_params.get("journal_file", "sep.journal")
                    sep_journal_file = os.path.join(journal_dir, journal_file_name)

                    main_py = os.path.join(main_dir, "main.py")
                    cmd = [os.path.expanduser("~/eclipse_env/bin/python3"), main_py, real_script, "--log-file", sep_log_file, "--journal-file", sep_journal_file]

                    if sep_params.get("test_mode") is True:
                        cmd.append("--test-mode")
                        logger.info("SEP lancé en mode test.")

                    log_level = sep_params.get("log_level")
                    if log_level:
                        cmd.extend(["--log-level", str(log_level)])
                        logger.info("Niveau de log SEP transmis: %s", log_level)
                    
                    if sep_params.get("strict_mode") is True:
                        cmd.append("--strict-mode")
                        logger.info("SEP lancé en mode strict.")

                    try:
                        logger.info(
                            "Lancement SEP (cwd=%s, command=%s)",
                            sep_dir,
                            " ".join(cmd),
                        )
                        with open(sep_log_file, "a") as log_fh:
                            proc = subprocess.Popen(
                                cmd,
                                cwd=sep_dir,
                                stdin=subprocess.DEVNULL,
                                stdout=log_fh,
                                stderr=log_fh,
                            )
                        try:
                            create_time = psutil.Process(proc.pid).create_time()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            # Rare race condition : process déjà terminé ou accès refusé
                            create_time = None
                            st.warning("Impossible de récupérer create_time du processus SEP : la vérification d'identité sera désactivée.")
                            logger.warning("create_time introuvable pour PID %s : vérification d'identité désactivée.", proc.pid)
                        st.session_state["sep_pid"] = proc.pid
                        st.session_state["sep_create_time"] = create_time
                        st.success(f"SEP lancé avec le PID {proc.pid}. Logs : {sep_log_file}")
                        logger.info("SEP lancé avec succès (pid=%s, create_time=%s).", proc.pid, create_time)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur au lancement de SEP : {e}")
                        logger.exception("Erreur au lancement du processus SEP")
