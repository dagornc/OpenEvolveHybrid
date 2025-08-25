import torch
import evaluate
import numpy as np
import optuna
from datasets import load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

# --- Configuration Globale ---
# Utiliser un modèle léger et un sous-ensemble du dataset pour aller plus vite
MODEL_NAME = "distilbert-base-uncased"
DATASET_NAME = "imdb"
# Pour un test rapide, on utilise un petit sous-ensemble des données
# Mettez `None` pour utiliser le dataset complet (beaucoup plus long !)
NUM_SAMPLES_TRAIN = 1000
NUM_SAMPLES_EVAL = 500

# --- 1. Chargement et préparation des données ---

print(f"Chargement du tokenizer pour le modèle {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print(f"Chargement du dataset {DATASET_NAME}...")
# On charge un petit sous-ensemble pour la rapidité
dataset = load_dataset(DATASET_NAME, split=f"train[:{NUM_SAMPLES_TRAIN}]+test[:{NUM_SAMPLES_EVAL}]")
# On divise à nouveau en train/test
dataset = dataset.train_test_split(test_size=0.3, shuffle=True, seed=42)

# Fonction pour tokeniser les données
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding=False)

print("Tokenisation du dataset...")
tokenized_datasets = dataset.map(tokenize_function, batched=True)
# On retire la colonne "text" qui n'est plus nécessaire et peut causer des erreurs
tokenized_datasets = tokenized_datasets.remove_columns(["text"])

# Data collator pour créer les batches de manière dynamique
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# --- 2. Définition de la fonction d'évaluation ---

print("Préparation de la métrique d'évaluation (accuracy)...")
accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy_metric.compute(predictions=predictions, references=labels)

# --- 3. Définition de la fonction "Objective" pour Optuna ---

# C'est ici que la magie opère.
# Optuna va appeler cette fonction à chaque "essai" (trial)
# avec une nouvelle combinaison d'hyperparamètres.
def objective(trial):
    # On charge un nouveau modèle à chaque essai pour éviter les poids pré-entraînés
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

    # Définition de l'espace de recherche des hyperparamètres
    training_args = TrainingArguments(
        output_dir=f"./results/trial_{trial.number}",
        # Hyperparamètres à optimiser
        learning_rate=trial.suggest_float("learning_rate", 1e-5, 5e-5, log=True),
        per_device_train_batch_size=trial.suggest_categorical("per_device_train_batch_size", [8, 16, 32]),
        num_train_epochs=trial.suggest_int("num_train_epochs", 1, 3),
        weight_decay=trial.suggest_float("weight_decay", 0.0, 0.3),

        # Arguments fixes
        per_device_eval_batch_size=16,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        logging_dir='./logs',
        logging_steps=50,
        disable_tqdm=False, # Mettre à True pour des logs plus propres
        report_to="none", # On désactive les intégrations (W&B, etc.)
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # Lancement de l'entraînement
    trainer.train()

    # Évaluation finale sur le set de test
    eval_result = trainer.evaluate()

    # On retourne la métrique qu'Optuna doit maximiser
    return eval_result["eval_accuracy"]

# --- 4. Lancement de l'étude d'optimisation ---

if __name__ == "__main__":
    # On vérifie si un GPU est disponible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Utilisation du device : {device}")

    # Création de l'étude Optuna.
    # La direction est "maximize" car nous voulons la plus grande accuracy possible.
    study = optuna.create_study(
        direction="maximize",
        study_name="huggingface_optimization",
        # Pruner: arrête les essais peu prometteurs en avance
        pruner=optuna.pruners.MedianPruner()
    )

    # Lancement de l'optimisation pour N essais
    # Augmentez le nombre d'essais pour une recherche plus exhaustive
    N_TRIALS = 10
    print(f"\nLancement de l'optimisation Optuna pour {N_TRIALS} essais...")
    study.optimize(objective, n_trials=N_TRIALS)

    # --- 5. Affichage des résultats ---
    print("\n=================================================")
    print("=== Optimisation terminée ! ===")
    print(f"Nombre d'essais terminés : {len(study.trials)}")
    print(f"Meilleur essai : Trial #{study.best_trial.number}")
    print(f"  Meilleure Accuracy : {study.best_trial.value:.4f}")
    print("  Meilleurs Hyperparamètres :")
    for key, value in study.best_trial.params.items():
        print(f"    - {key}: {value}")
    print("=================================================")

    # Vous pouvez visualiser les résultats avec `optuna-dashboard`
    # sqlite:///huggingface_optimization.db
    # (Nécessite `pip install optuna-dashboard`)
