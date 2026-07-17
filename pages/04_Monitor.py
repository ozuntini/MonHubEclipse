#!/usr/bin/env python3
"""
Eclipse Photography — Monitoring Dashboard (Streamlit)

Reads the JSONL action journal and displays in real-time:
  - the last completed action
  - the next scheduled action

Usage:
    streamlit run monitor_dashboard.py -- --journal eclipse_journal.jsonl
"""

import json
import sys
import time
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# How often the dashboard auto-refreshes for the clock (seconds)
REFRESH_CLOCK_SECONDS = 1

# How often the JSONL journal file is re-read (seconds)
REFRESH_JOURNAL_SECONDS = 10

# Configuration du nom du fichier journal et création du dossier de logs s'il n'existe pas
# Récupérer le chemin du dossier de log dans le fichier sep_params.json
SEP_PARAMS_PATH = os.path.expanduser("~/Eclipse_Project/sep_params.json")

if os.path.exists(SEP_PARAMS_PATH):
    with open(SEP_PARAMS_PATH, "r", encoding="utf-8") as f:
        sep_params = json.load(f)
    LOG_DIR = sep_params.get("log_dir", os.path.expanduser("~/Eclipse_Project/logs"))
else:
    LOG_DIR = os.path.expanduser("~/Eclipse_Project/logs")

# Récupérer le chemin du dossier journal dans le fichier sep_params.json
if os.path.exists(SEP_PARAMS_PATH):
    with open(SEP_PARAMS_PATH, "r", encoding="utf-8") as f:
        sep_params = json.load(f)
    JOURNAL_DIR = sep_params.get("journal_dir", os.path.expanduser("~/Eclipse_Project/logs"))
else:
    JOURNAL_DIR = os.path.expanduser("~/Eclipse_Project/logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if not os.path.exists(JOURNAL_DIR):
    os.makedirs(JOURNAL_DIR)

# Récupérer le chemin du fichier journal dans le fichier sep_params.json
if os.path.exists(SEP_PARAMS_PATH):
    with open(SEP_PARAMS_PATH, "r", encoding="utf-8") as f:
        sep_params = json.load(f)
    JOURNAL_FILE = sep_params.get("journal_file", "eclipse_journal.json")
    JOURNAL_FILE = os.path.join(JOURNAL_DIR, JOURNAL_FILE)
else:
    JOURNAL_FILE = os.path.join(JOURNAL_DIR, "eclipse_journal.json")

# Configuration du logger

logger = logging.getLogger("monitor")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "monitor.log"))
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

logger.debug(
    "Configuration monitor initialisée (sep_params=%s, log_dir=%s, journal_dir=%s, journal_file=%s)",
    SEP_PARAMS_PATH,
    LOG_DIR,
    JOURNAL_DIR,
    JOURNAL_FILE,
)


# ---------------------------------------------------------------------------
# Argument parsing (Streamlit strips everything before "--")
# ---------------------------------------------------------------------------

def _get_journal_path() -> str:
    """Return the journal file path from CLI args or default."""
    args = sys.argv[1:]
    try:
        idx = args.index("--journal")
    except ValueError:
        logger.debug("Argument --journal absent, journal par defaut utilise: %s", JOURNAL_FILE)
        return JOURNAL_FILE
    if idx + 1 >= len(args):
        print(
            "[monitor_dashboard] Warning: --journal requires a value; using default.",
            file=sys.stderr,
        )
        logger.warning("Argument --journal sans valeur, journal par defaut utilise: %s", JOURNAL_FILE)
        return JOURNAL_FILE
    resolved = args[idx + 1]
    logger.debug("Journal fourni via CLI: %s", resolved)
    return resolved

# ---------------------------------------------------------------------------
# Journal reading helpers
# ---------------------------------------------------------------------------

ACTION_EVENTS = {"PHOTO_TRIGGER", "FILTER_MOVE", "ACTION_COMPLETE", "ACTION_START", "CIRCUMSTANCE"}

EVENT_ICONS = {
    "PHOTO_TRIGGER": "📷",
    "FILTER_MOVE": "😎",
    "ACTION_COMPLETE": "✅",
    "ACTION_START": "🕔",
    "SESSION_START": "🚀",
    "SESSION_END": "🏁",
    "CIRCUMSTANCE": "⏱️",
}


def _parse_journal(path: str) -> list[dict]:
    """Read *all* valid JSON lines from the journal and return them as a list."""
    entries: list[dict] = []
    p = Path(path)
    if not p.exists():
        logger.warning("Fichier journal introuvable: %s", path)
        return entries
    try:
        with p.open("r", encoding="utf-8") as fh:
            malformed_count = 0
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    malformed_count += 1
                    logger.warning("Ligne JSON invalide ignoree dans %s: %s", path, exc)
        if malformed_count > 0:
            logger.warning("Lecture journal terminee avec %s ligne(s) invalide(s): %s", malformed_count, path)
        logger.info("Journal lu: %s entree(s) valides depuis %s", len(entries), path)
    except OSError:
        logger.exception("Erreur d'E/S pendant la lecture du journal: %s", path)
    return entries


def _last_action_entry(entries: list[dict]) -> dict | None:
    """Return the most recent entry whose event is in ACTION_EVENTS."""
    for entry in reversed(entries):
        if entry.get("event") in ACTION_EVENTS:
            return entry
    return None


# ---------------------------------------------------------------------------
# UI rendering helpers
# ---------------------------------------------------------------------------

def _status_widget(status: str) -> None:
    """Render status with appropriate Streamlit component."""
    if status == "SUCCESS":
        icon="✅"
    elif status == "ERROR":
        icon="❌"
    elif status == "SKIPPED":
        icon="⚠️"
    elif status == "PENDING":
        icon="⏳"
    else:
        icon="ℹ️"
    st.info(status, icon=icon)

def _render_last_action(entry: dict) -> None:
    """Render the 'Dernière action réalisée' block."""
    event = entry.get("event", "")
    icon = EVENT_ICONS.get(event, "⚙️")
    current = entry.get("current_action") or {}
    details = entry.get("details") or {}
    timestamp = entry.get("timestamp", '—')
    if isinstance(timestamp, str):
        try:
            # Accept ISO timestamp with optional microseconds/timezone.
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    with st.container(border=True):
        st.subheader(f"{icon} Action en cours")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Timestamp :** {timestamp}")
            st.write(f"**Séquence n° :** {current.get('index', '—') + 1}")
            st.write(f"**Événement :** `{event}`")
        with col2:
            st.write(f"**Description :** {current.get('description', '—')}")
            _status_widget(str(entry.get("status", "—")))

        # Extra details per event type
        if event == "PHOTO_TRIGGER":
            ok = details.get("cameras_success", "?")
            total = details.get("cameras_total", "?")
            st.write(f"📸 Appareils déclenchés : **{ok} / {total}**")
        elif event == "FILTER_MOVE":
            direction_raw = details.get("direction", "")
            direction_label = {
                "OPEN": "Ouverture ⤴️",
                "CLOSE": "Fermeture ⤵️",
            }.get(str(direction_raw).upper(), direction_raw)
            st.write(f"😎 Direction du filtre : **{direction_label}**")


def _render_filter_status(entry: dict) -> None:
    """Render a block specifically for the last FILTER_MOVE status, if any."""
    with st.container(border=True):
        st.subheader("😎 Dernier mouvement du filtre")
        # Find the most recent FILTER_MOVE entry
        for e in reversed(st.session_state.entries):
            if e.get("event") == "FILTER_MOVE":
                details = e.get("details") or {}
                direction_raw = details.get("direction", "")
                direction_label = {
                    "OPEN": "Ouverture ⤴️",
                    "CLOSE": "Fermeture ⤵️",
                }.get(str(direction_raw).upper(), direction_raw)
                status = e.get("status", "—")
                st.info(f"Direction : **{direction_label}** (status: {status})")
                return
        st.info("Aucun mouvement de filtre enregistré pour le moment.")

def _render_battery_status(entry: dict) -> None:
    """Render a block specifically for the last battery status, if any."""
    with st.container(border=True):
        st.subheader("🔋 Dernier statut de batterie")
        # Find the most recent CAMERA_HEALTH entry
        for e in reversed(st.session_state.entries):
            if e.get("event") != "CAMERA_HEALTH":
                continue
            details = e.get("details") or {}
            if "battery_percentage" in details:
                battery_percentage = details.get("battery_percentage", "—")
                battery_text = str(battery_percentage)
                if battery_text not in {"", "—"} and not battery_text.endswith("%"):
                    battery_text = f"{battery_text}%"
                last_read = _format_health_timestamp(e.get("timestamp"))
                # Display battery status with last read time
                # use st.info if battery status > 20%, st.warning if between 10% and 20%, st.error if < 10%
                try:
                    battery_value = float(battery_percentage)
                    if battery_value >= 20:
                        st.info(
                            f"Pourcentage batterie : **{battery_text}**\n\n",
                            icon="🔋"
                        )
                    elif 10 <= battery_value < 20:
                        st.warning(
                            f"Pourcentage batterie : **{battery_text}**\n\n",
                            icon="🪫"
                        )
                    else:
                        st.error(
                            f"Pourcentage batterie : **{battery_text}**\n\n",
                            icon="⚠️"
                        )
                except (TypeError, ValueError):
                    st.info(
                        f"Pourcentage batterie : **{battery_text}**\n\n",
                        icon="🔋"
                    )
                st.caption(
                    f"⏰ Dernière lecture : **{last_read}**"
                )
                return
        st.info("Aucun statut de batterie enregistré pour le moment.")

def _render_next_action(entry: dict) -> None:
    """Render the 'Prochaine action' block."""
    next_action = entry.get("next_action")

    with st.container(border=True):
        st.subheader("⏭️ Prochaine action")
        if next_action:
            type = next_action.get("type", "—")
            if type == "PHOTO":
                icon = "📷"
            elif type == "FILTER":
                icon = "😎"
            else:
                icon = "❓"

            st.write(f"**Type :** `{type}` - `{icon}`")
            st.write(f"**Description :** {next_action.get('description', '—')}")
            scheduled = next_action.get("scheduled_at")
            st.write(f"**Heure prévue :** {scheduled if scheduled else '—'}")
        else:
            st.info("✅ Séquence terminée — aucune action suivante")


def _render_history(entries: list[dict]) -> None:
    """Render the last-10-entries expander."""
    with st.expander("📋 Historique récent", expanded=False):
        if not entries:
            st.write("Aucune entrée disponible.")
            return

        recent = entries[-10:]
        rows = []
        for e in reversed(recent):
            current = e.get("current_action") or {}
            rows.append(
                {
                    "timestamp": e.get("timestamp", ""),
                    "seq": e.get("seq", ""),
                    "event": e.get("event", ""),
                    "description": current.get("description", ""),
                    "status": e.get("status", ""),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch")

def _time_line(circonstances: dict) -> None:
    """ Render a simple timeline visualization of the sequence progress.
        Calculate and display the delay to the next active circumstance (C1, C2, Max, C3, C4).
        Automatically advance to the next one when the current is exceeded. """
    
    # List of circumstances in order
    circumstance_keys = {"C1": "Premier contact", "C2": "Deuxième contact", "Max": "Maximum", "C3": "Troisième contact", "C4": "Quatrième contact"}
    
    # Parse all circumstance timestamps
    parsed = {}
    for key in circumstance_keys:
        ts_str = circonstances.get(key, "")
        if ts_str:
            try:
                # Try full ISO format first (with or without microseconds)
                ts_str_clean = ts_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_str_clean)
                # Convert to naive if it has timezone info
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                parsed[key] = dt
            except (ValueError, AttributeError):
                # Try parsing as HH:MM:SS and combine with today's date
                try:
                    time_obj = datetime.strptime(ts_str.strip(), "%H:%M:%S").time()
                    dt = datetime.combine(datetime.now().date(), time_obj)
                    parsed[key] = dt
                except (ValueError, AttributeError):
                    parsed[key] = None
        else:
            parsed[key] = None
    
    # Get current time as naive datetime for consistent comparison
    now = datetime.now()
    
    # Find the next active circumstance (not yet exceeded)
    active_key = None
    next_delay = None
    
    for key in circumstance_keys:
        if parsed[key] and parsed[key] > now:
            active_key = key
            next_delay = parsed[key] - now
            break
    
    
    if active_key and next_delay:
        hours, remainder = divmod(int(next_delay.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        icon="⏱️"
        if hours <= 0:
            delay_str = f"{minutes:02d} min {seconds:02d} sec"
            if minutes <= 0:
                delay_str = f"{seconds:02d} sec"
                icon = "⚠️"
                st.warning(f"**{delay_str}** avant le {circumstance_keys[active_key]}", icon=icon)
                return
        else:
            delay_str = f"{hours:02d}h {minutes:02d} min {seconds:02d} sec"
        st.info(f"**{delay_str}** avant le {circumstance_keys[active_key]}", icon=icon)
    else:
        st.warning(f"Toutes les circonstances sont dépassées ou indéfinies", icon="⚠️")



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_last_read_ts(ts: float | None) -> str:
    """Return a human-readable last-read timestamp, or 'Jamais' if not yet read."""
    if ts is None:
        return "Jamais"
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def _format_health_timestamp(timestamp: Any) -> str:
    """Return a readable HH:MM:SS from an ISO timestamp, fallback to raw value."""
    if not isinstance(timestamp, str) or not timestamp:
        return "—"
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%H:%M:%S")
    except ValueError:
        return timestamp

def _reading_circumstance(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract event = CIRCUMSTANCE and get information about the current circumstance."""
    for e in reversed(entries):
        if e.get("event") == "CIRCUMSTANCE":
            return e.get("information") or {}
    return {}

# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

def main() -> None:
    # -- if argument --journal is provided, use it; otherwise use journal_file from sep_params.json
    journal_path = _get_journal_path()

    st.set_page_config(
        page_title="Eclipse Photography — Monitoring",
        page_icon="🌑",
        layout="wide",
    )

    # --- Session state init ---
    if "last_log_read_ts" not in st.session_state:
        st.session_state.last_log_read_ts = None  # triggers immediate read on first run
        st.session_state.entries = []
        st.session_state.last_entry = None
        st.session_state.total_lines = 0
        st.session_state.monitor_log_bootstrap_done = False

    if not st.session_state.monitor_log_bootstrap_done:
        logger.info("Dashboard monitor initialise. Journal surveille: %s", journal_path)
        st.session_state.monitor_log_bootstrap_done = True

    # --- Header ---
    st.title("🌑 Eclipse Photography — Monitoring en temps réel")
    
    # --- Circumstances ---
    entries = st.session_state.entries
    circonstances = _reading_circumstance(entries)
    if circonstances:
        st.subheader(
            f"C1 {circonstances.get('C1', '—')} - "
            f"C2 {circonstances.get('C2', '—')} - "
            f"Max {circonstances.get('Max', '—')} - "
            f"C3 {circonstances.get('C3', '—')} - "
            f"C4 {circonstances.get('C4', '—')}",
            text_alignment="center"
        )
    
    st.divider()
    
    # --- Time Line + digital clock ---
    time_line_col, clock_col = st.columns([3, 1])
    with time_line_col:
        _time_line(circonstances)
    with clock_col:
        st.markdown(
            f"<div style='text-align:right; font-size:2rem; font-weight:bold; "
            f"font-family:monospace; padding-top:0.5rem;'>"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}</div>",
            unsafe_allow_html=True,
        )

    # --- Conditionally re-read journal (every 10 s) ---
    now_ts = time.time()
    if (
        st.session_state.last_log_read_ts is None
        or now_ts - st.session_state.last_log_read_ts >= REFRESH_JOURNAL_SECONDS
    ):
        st.session_state.last_log_read_ts = now_ts
        entries = _parse_journal(journal_path)
        st.session_state.entries = entries
        st.session_state.total_lines = len(entries)
        st.session_state.last_entry = _last_action_entry(entries)
        logger.info(
            "Mise a jour journal: total=%s, derniere_action=%s",
            st.session_state.total_lines,
            (st.session_state.last_entry or {}).get("event", "none"),
        )

    entries = st.session_state.entries
    last_entry = st.session_state.last_entry
    total_lines = st.session_state.total_lines
    circonstances = _reading_circumstance(entries)

    # Test-mode banner (shown if any entry has test_mode == True)
    if any((e.get("details") or {}).get("test_mode") for e in entries):
        st.warning("🧪 **Mode test activé** — aucune photo réelle ne sera prise")
        if not st.session_state.get("monitor_test_mode_logged", False):
            logger.warning("Mode test detecte dans le journal.")
            st.session_state.monitor_test_mode_logged = True

    # --- No data state ---
    if not entries or last_entry is None:
        file_exists = Path(journal_path).exists()
        if not file_exists:
            st.info(
                "⏳ En attente du démarrage de la séquence... (fichier non trouvé)"
            )
        else:
            st.info("⏳ En attente du démarrage de la séquence...")
        st.divider()
        last_read_str = _format_last_read_ts(st.session_state.last_log_read_ts)
        st.caption(
            f"Entrées lues : {total_lines}  •  "
            f"Dernière lecture du journal : "
            f"{last_read_str}"
        )
        time.sleep(REFRESH_CLOCK_SECONDS)
        st.rerun()


    # --- Last action block + Next action block ---
    last_action_col, next_action_col = st.columns(2)
    with last_action_col:
        # --- Last action block ---
        _render_last_action(last_entry)

    with next_action_col:
        # --- Next action block ---
        _render_next_action(last_entry)

    # --- Status block + Image block ---
    status_col, image_col = st.columns([3, 1])
    # --- Status block ---
    with status_col:
        battery_status_col, filter_status_col = st.columns(2)
        # --- battery_status_col + filter_status_col ---
        with battery_status_col:
            _render_battery_status(last_entry)

        with filter_status_col:
            _render_filter_status(last_entry)
    # --- Image block ---
    with image_col:
        # if image file exists, show it; otherwise show message and try to show it anyway (in case it appears between the check and the display)
        image_path = "/home/ozuntini/Eclipse_Project/capture/capture_preview.jpg"
        if Path(image_path).exists():
            st.image(image_path, caption="capture_preview.jpg")
        else:
            st.info("Aucune image de prévisualisation disponible.", icon="⚠️")
            try:
                st.image(image_path, caption="capture_preview.jpg")
            except Exception:
                pass

    st.divider()
    
    # --- History ---
    _render_history(entries)

    # --- Status bar ---
    last_read_str = _format_last_read_ts(st.session_state.last_log_read_ts)
    st.caption(
        f"Entrées lues : {total_lines}  •  "
        f"Dernière lecture du journal : "
        f"{last_read_str}"
        f"  ➡️  Fichier journal surveillé : `{journal_path}`"
    )

    # --- Auto-refresh every 1 s (for the clock) ---
    time.sleep(REFRESH_CLOCK_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
