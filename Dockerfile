# Utiliser une image Python 3.12 officielle comme base pour correspondre à l'environnement cible
FROM python:3.12-slim

# Définir l'auteur du fichier
LABEL maintainer="Jules"

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier le fichier des dépendances d'abord pour profiter du cache Docker
COPY requirements.txt .

# Mettre à jour pip et installer les dépendances
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier les répertoires de l'application et le point d'entrée
COPY alpha_evolver/ ./alpha_evolver/
COPY config/ ./config/
COPY main.py .

# La commande par défaut pour exécuter l'application
# Note: Le répertoire du code source à optimiser doit être monté en tant que volume
# lors de l'exécution du conteneur (ex: -v /path/to/your/code:/root/projets)
CMD ["python", "main.py"]
