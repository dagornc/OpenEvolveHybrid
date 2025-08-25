# Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Définir l'auteur du fichier (bonne pratique)
LABEL maintainer="Jules"

# Empêcher Python de mettre en mémoire tampon les sorties stdout et stderr
# C'est utile pour voir les logs en temps réel depuis le conteneur
ENV PYTHONUNBUFFERED=1

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances
# --no-cache-dir permet de réduire la taille de l'image
#
# NOTE SUR LE GPU:
# Pour utiliser un GPU, vous devez :
# 1. Utiliser une image de base compatible CUDA, ex: nvidia/cuda:11.8.0-base-ubuntu22.04
# 2. Installer PyTorch avec le support CUDA. Vous devriez modifier requirements.txt
#    ou lancer la commande pip install torch --index-url ... ici.
# 3. Installer le NVIDIA Container Toolkit sur votre machine hôte.
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code du projet dans le répertoire de travail
COPY openevolve_project/ ./openevolve_project/

# Définir le répertoire de travail sur celui du projet pour que le script trouve config.toml
WORKDIR /app/openevolve_project

# Commande à exécuter lorsque le conteneur est lancé
CMD ["python", "optimize.py"]
