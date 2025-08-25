# Optimisation d'Algorithmes Hugging Face avec Optuna (et Docker)

Ce projet fournit un environnement conteneurisé avec Docker pour optimiser les hyperparamètres de modèles Hugging Face en utilisant Optuna.

## Objectif

L'objectif est de fournir un moyen simple, reproductible et portable pour lancer des expériences d'optimisation d'hyperparamètres. La configuration des expériences se fait via un simple fichier `config.toml`.

## Contenu du Projet

- `Dockerfile`: Le plan de construction de l'image Docker.
- `requirements.txt`: La liste des dépendances Python.
- `openevolve_project/`: Le répertoire contenant le code source.
  - `optimize.py`: Le script Python qui lance l'optimisation.
  - `config.toml`: **Le fichier de configuration principal.** C'est ici que vous définissez le modèle, le dataset, etc.
- `setup.sh`: (Alternative) Un script pour une installation manuelle sans Docker.

---

## Méthode Recommandée : Utilisation avec Docker

Cette méthode est la plus simple et garantit la reproductibilité.

### Prérequis
- Docker doit être installé sur votre machine.

### Étape 1 : Configurer votre expérience

Avant de construire l'image, modifiez le fichier `openevolve_project/config.toml` pour définir votre expérience :
```toml
# openevolve_project/config.toml

[model]
name = "distilbert-base-uncased" # Nom du modèle

[dataset]
name = "imdb" # Nom du dataset
num_samples_train = 1000 # -1 pour le dataset complet
num_samples_eval = 500   # -1 pour le dataset complet

[optimization]
n_trials = 15 # Nombre d'essais Optuna
study_name = "hf_study_docker" # Nom de la base de données de résultats
```

### Étape 2 : Construire l'image Docker

À la racine du projet, lancez la commande suivante. L'option `-t` permet de donner un nom à votre image (par exemple, `hf-optimizer`).
```bash
docker build -t hf-optimizer .
```
Cette commande va lire le `Dockerfile`, télécharger les dépendances et créer votre image. Cela peut prendre plusieurs minutes la première fois.

### Étape 3 : Lancer l'optimisation

Une fois l'image construite, lancez un conteneur. Les résultats (`.db` et logs) seront créés à l'intérieur du conteneur.
```bash
docker run --rm hf-optimizer
```
- `--rm` : Supprime le conteneur automatiquement après son exécution.

Pour extraire les résultats (la base de données SQLite), vous pouvez monter un volume :
```bash
# Crée un dossier "results" sur votre machine hôte
mkdir -p results

# Monte le dossier /app/openevolve_project/results du conteneur
# vers le dossier "results" de votre machine hôte.
docker run --rm -v "$(pwd)/results:/app/openevolve_project/results" hf-optimizer
```

---

## Visualiser les Résultats

Après avoir extrait la base de données (ex: `hf_study_docker.db`), vous pouvez utiliser `optuna-dashboard`.

1.  **Installez le dashboard** sur votre machine locale :
    ```bash
    pip install optuna-dashboard
    ```
2.  **Lancez le serveur** en pointant vers le fichier `.db` :
    ```bash
    optuna-dashboard sqlite:///results/hf_study_docker.db
    ```

---

## Alternative : Installation Manuelle (sans Docker)

Si vous ne souhaitez pas utiliser Docker, vous pouvez utiliser le script `setup.sh`.

1.  **Rendre le script exécutable :**
    ```bash
    chmod +x setup.sh
    ```
2.  **Lancer le script :**
    ```bash
    ./setup.sh
    ```
3.  **Activer l'environnement et lancer le script :**
    ```bash
    cd openevolve_project
    source env/bin/activate
    python optimize.py
    ```
Cette méthode est moins portable et dépend de la configuration de votre système d'exploitation (conçu pour Debian/Ubuntu).
