#!/bin/bash
# Script de test lancement pour Solar_Eclipse_Photography Python

set -e
# Définir une fonction d'erreur
on_error() {
    if [ -n "$VIRTUAL_ENV" ]; then
        # Désactivation de l'environnement virtuel et sortie avec code d'erreur
        echo "Désactivation de l'environnement virtuel et sortie sur erreur..."
        deactivate
    fi
    exit 1
}

# Capturer les erreurs
trap 'on_error' ERR

echo "=== Lanceur Accueil Mon Hub Eclipse ==="

if [ "$1" == "-h" ] || [ "$#" -lt 0 ]; then
    echo "usage: ./MHE_launcher.sh"
    exit
fi

# Activation de l'environnement virtuel si disponible
if [ -f ~/eclipse_env/bin/activate ]; then
    echo "Activation de l'environnement virtuel..."
    source ~/eclipse_env/bin/activate
fi

# Lancement du script principal
echo "Lancement du script principal..."
echo "Command: streamlit run Accueil.py"
echo ""
echo "===================================="
sleep 1
streamlit run Accueil.py

# Désactivation de l'environnement virtuel
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Désactivation de l'environnement virtuel..."
    deactivate
fi

# Fin du script
