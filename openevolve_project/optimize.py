import torch
import evaluate
import numpy as np
import optuna
import toml
from datasets import load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

# --- 1. Définition de la fonction d'évaluation ---
# Pas de changement ici, mais on la place avant pour la clarté

accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy_metric.compute(predictions=predictions, references=labels)


# --- 2. Définition de la fonction "Objective" pour Optuna ---

# La fonction objective est maintenant plus générique.
# Elle prend en paramètre les éléments qui dépendent de la configuration.
def objective_factory(model_name, tokenized_datasets, data_collator):
    """Crée la fonction objective pour Optuna."""

    def objective(trial):
        # On charge un nouveau modèle à chaque essai pour éviter les poids pré-entraînés
        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

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
            disable_tqdm=False,
            report_to="none",
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_datasets["train"],
            eval_dataset=tokenized_datasets["test"],
            data_collator=data_collator,
            compute_metrics=compute_metrics,
        )

        trainer.train()
        eval_result = trainer.evaluate()
        return eval_result["eval_accuracy"]

    return objective

# --- 3. Fonction Principale ---

def main():
    # Chargement de la configuration depuis le fichier TOML
    print("Chargement de la configuration depuis config.toml...")
    config = toml.load("config.toml")

    model_config = config["model"]
    dataset_config = config["dataset"]
    optim_config = config["optimization"]

    # On vérifie si un GPU est disponible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Utilisation du device : {device}")

    # --- Préparation des données (déplacé dans main) ---
    print(f"Chargement du tokenizer pour le modèle {model_config['name']}...")
    tokenizer = AutoTokenizer.from_pretrained(model_config['name'])

    print(f"Chargement du dataset {dataset_config['name']}...")
    # Gestion de l'utilisation du dataset complet si num_samples est -1
    train_split = f"train[:{dataset_config['num_samples_train']}]" if dataset_config['num_samples_train'] > 0 else "train"
    test_split = f"test[:{dataset_config['num_samples_eval']}]" if dataset_config['num_samples_eval'] > 0 else "test"
    dataset = load_dataset(dataset_config['name'], split=f"{train_split}+{test_split}")

    dataset = dataset.train_test_split(test_size=0.3, shuffle=True, seed=42)

    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, padding=False)

    print("Tokenisation du dataset...")
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    tokenized_datasets = tokenized_datasets.remove_columns(["text"])
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # --- Lancement de l'étude d'optimisation ---
    study = optuna.create_study(
        direction="maximize",
        study_name=optim_config['study_name'],
        pruner=optuna.pruners.MedianPruner()
    )

    # Création de la fonction objective avec les bons paramètres
    objective_func = objective_factory(
        model_name=model_config['name'],
        tokenized_datasets=tokenized_datasets,
        data_collator=data_collator
    )

    n_trials = optim_config['n_trials']
    print(f"\nLancement de l'optimisation Optuna pour {n_trials} essais...")
    study.optimize(objective_func, n_trials=n_trials)

    # --- Affichage des résultats ---
    print("\n=================================================")
    print("=== Optimisation terminée ! ===")
    print(f"Nombre d'essais terminés : {len(study.trials)}")
    print(f"Meilleur essai : Trial #{study.best_trial.number}")
    print(f"  Meilleure Accuracy : {study.best_trial.value:.4f}")
    print("  Meilleurs Hyperparamètres :")
    for key, value in study.best_trial.params.items():
        print(f"    - {key}: {value}")
    print("=================================================")
    print(f"\nPour visualiser les résultats, lancez :")
    print(f"optuna-dashboard sqlite:///{optim_config['study_name']}.db")

if __name__ == "__main__":
    main()
