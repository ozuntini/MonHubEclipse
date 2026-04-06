import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mon Hub Eclipse", layout="centered")

st.title("😎 Hub Eclipse 😎")
st.write("""
Cette interface regroupe tous mes outils Python d'observation des éclipses Solaires ou Lunaires.  
Utilisez la **barre latérale à gauche** pour naviguer entre les différentes applications.
""")

st.info("Le menu à gauche est généré automatiquement à partir du dossier 'pages/'.")