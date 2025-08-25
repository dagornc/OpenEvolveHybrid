#!/bin/bash
#
# Script de configuration pour un environnement d'optimisation
# d'algorithmes Hugging Face avec Optuna sur un VPS Debian/Ubuntu.
#
# Auteur: Jules
#

# Arrête le script en cas d'erreur
set -e

echo "================================================================="
echo "=== Lancement du script de configuration pour OpenEvolve/HF ==="
echo "================================================================="

# --- 1. Mise à jour du système ---
echo -e "\n[ÉTAPE 1/6] Mise à jour des paquets système..."
sudo apt-get update && sudo apt-get upgrade -y

# --- 2. Installation des dépendances système ---
echo -e "\n[ÉTAPE 2/6] Installation des dépendances (python3, pip, venv, git)..."
sudo apt-get install -y python3-pip python3.10-venv git build-essential

# --- 3. Création du répertoire de projet ---
PROJECT_DIR="openevolve_project"
echo -e "\n[ÉTAPE 3/6] Création du répertoire de projet : $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# --- 4. Création de l'environnement virtuel ---
VENV_NAME="env"
echo -e "\n[ÉTAPE 4/6] Création de l'environnement virtuel Python : $VENV_NAME"
python3 -m venv $VENV_NAME

# Activation de l'environnement virtuel pour la suite du script
source $VENV_NAME/bin/activate

echo "Environnement virtuel activé."

# --- 5. Installation des librairies Python ---
echo -e "\n[ÉTAPE 5/6] Installation des librairies Python..."

# Mise à jour de pip
pip install --upgrade pip

# Détection du GPU et installation de PyTorch
if command -v nvidia-smi &> /dev/null; then
    echo "GPU NVIDIA détecté ! Installation de PyTorch avec support CUDA."
    # Vous pouvez changer la version de CUDA (ex: cu117, cu121) selon votre driver
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "Aucun GPU NVIDIA détecté. Installation de la version CPU de PyTorch."
    pip install torch torchvision torchaudio
fi

echo "Installation de Hugging Face, Optuna et autres librairies utiles..."
pip install transformers datasets accelerate evaluate scikit-learn pandas optuna huggingface_hub

# --- 6. Finalisation ---
echo -e "\n[ÉTAPE 6/6] Configuration terminée avec succès !"
echo "================================================================="
echo -e "\nPour commencer à travailler, suivez ces étapes :"
echo "1. Accédez au répertoire du projet :"
echo "   cd $PROJECT_DIR"
echo ""
echo "2. Activez l'environnement virtuel (si ce n'est pas déjà fait) :"
echo "   source $VENV_NAME/bin/activate"
echo ""
echo "3. (Recommandé) Connectez-vous à votre compte Hugging Face :"
echo "   huggingface-cli login"
echo "   (Vous aurez besoin d'un token d'accès que vous pouvez trouver sur huggingface.co/settings/tokens)"
echo ""
echo "Vous êtes maintenant prêt à lancer vos scripts d'optimisation !"
echo "================================================================="

# Désactivation de l'environnement pour ne pas affecter le shell courant
deactivate
