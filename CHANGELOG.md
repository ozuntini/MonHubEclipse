# Changelog

Tous les changements notables pour ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/),
et ce projet adhère à [Semantic Versioning](https://semver.org/).

---

## [Version 1.0.1] - 2026-05-16
### Ajouté (Added)
- Documentation sur la création d'un service pour lancer automatiquement le Hub.
- Installeur du service systemd (install.sh)

### Modifié (Changed)
- Mise à jour du README.md.

### Corrigé (Fixed)
- 

### Supprimé (Removed)
- 

## [Version 1.0.0] - 2026-05-15
### Ajouté (Added)
- Versioning de l'application
- Entête du fichier Changelog.md

### Modifié (Changed)
- Rotation des fichiers de logs par bouton dans 05_logs.py.  
Le fichier aaaaa.log et renommé en aaaaa.log.datetime.now.
- Formatage du fichier Changelog
- Modification de la présantation des actions en cours et de la prochaine action pour améliorer la lisibilité
- Modification de l'affichage des circonstances de l'éclipse

### Corrigé (Fixed)
- Correction du double affichage de l'historique récent

### Supprimé (Removed)
- Renommage des log en log.old.

## 2026/05/03
- Modification de la mise en page du moniteur
- Récupération et affichage des circonstances locales de l'éclipse, des status de batterie et de filtre
- Corrections diverses
- Amélioration de l'affichage de la timeline

## 2026/05/01
- Ajout du moniteur
- Restructuration de l'affichage du moniteur

## 2026/04/28
- Correction de la gestion des marges avant et après sur le graphique

## 2026/04/27
- Correction de la gestion des logs pour écrire dans des fichiers différents.
- Gestion des graphiques pour une heure > 23h

## 2026/04/26
- Modification du fichier log
- Adaptation pour le regroupement dans Eclipse Project

## 2026/02/19
- Corrections suite à un test de réinstallation complète
- Ajout du chargement de la librairie Filter.controler
- Amélioration de la gestion du journal des check 

## 2026/04/18
- Création du Verification.py pour contrôler la config du boitier avant de commencer
- Ajout de la partie vérification manuelle
- ajout du bouton pour synchroniser l'horloge du boitier et du PC
- ajout d'un journal des checks

## 2026/04/14
- Modification du setfilter pour forcer le cycle de configuration des positions Open et Closed
- Ajout de la fonction de vérification du setting
- Cycle de réglage contraint, obligation de valider le set 1 avant le 2

## 2026/04/12
- Création du lanceur MHE_Launcher.sh
- Adaptation au passage de filter_controler en package

## 2026/04/11
- Création du SetFilter.py
- Corrections diverses de Horaires.py
- Finalisation du SetFilter.py
- Centralisation des logs

## 2026/04/08
- Ajout de la gestion des fichiers existants
- gestion de la rotation des logs
- Création d'un fichier header

## 2026/04/06
- Création des programmes
- Premier commit