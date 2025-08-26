import os
import subprocess
import time
import difflib
import re
from configparser import ConfigParser
from typing import List, Dict, Any

# Supposons que llm_provider.py et son contenu existent déjà
# from .llm_provider import get_llm_provider


# --- Agent 1: Chargement du Code ---

def load_code_from_disk(config: ConfigParser) -> Dict[str, str]:
    """
    Charge tous les fichiers .py depuis le répertoire source spécifié dans la config.

    Args:
        config: L'objet de configuration chargé.

    Returns:
        Un dictionnaire où les clés sont les chemins des fichiers et les valeurs
        sont le contenu de ces fichiers.
    """
    source_dir = config.get('paths', 'source_directory')
    print(f"Chargement du code depuis le répertoire : {source_dir}")

    code_files = {}
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(f"Le répertoire source '{source_dir}' n'existe pas.")

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    code_files[filepath] = f.read()

    if not code_files:
        raise ValueError(f"Aucun fichier .py trouvé dans '{source_dir}'.")

    print(f"{len(code_files)} fichier(s) Python chargé(s).")
    return code_files


# --- Agent 2: Génération des Variations ---

def generate_code_variations(original_code: Dict[str, str], llm_client: Any, config: ConfigParser) -> List[Dict[str, str]]:
    """
    Utilise le LLM pour générer plusieurs variations du code original.
    """
    prompt_template = config.get('evolution', 'optimization_prompt')
    num_variations = config.getint('evolution', 'variations_per_generation')

    # Pour cette implémentation, nous nous concentrons sur l'optimisation d'un seul fichier.
    # Une approche plus complexe gérerait les dépendances inter-fichiers.
    target_filepath, code_content = next(iter(original_code.items()))

    print(f"Génération de {num_variations} variations pour le fichier : {target_filepath}...")

    full_prompt = f"""
    {prompt_template}

    Voici le code original du fichier `{target_filepath}`:
    ```python
    {code_content}
    ```

    Génère {num_variations} version(s) améliorée(s) de ce code.
    Réponds UNIQUEMENT avec le code Python, chaque version étant dans un bloc de code markdown séparé et clairement identifié.
    Par exemple:
    ### Version 1
    ```python
    # code de la version 1...
    ```
    ### Version 2
    ```python
    # code de la version 2...
    ```
    """

    print("Envoi de la requête au LLM...")
    response_text = llm_client.invoke(full_prompt)

    print("Réponse du LLM reçue. Analyse des variations...")

    # Utiliser regex pour trouver tous les blocs de code Python
    code_blocks = re.findall(r'```python\n(.*?)\n```', response_text, re.DOTALL)

    if not code_blocks:
        print("AVERTISSEMENT: Aucun bloc de code valide n'a été trouvé dans la réponse du LLM.")
        return []

    variations = []
    for i, code_block in enumerate(code_blocks):
        print(f"Variation {i+1} extraite.")
        variations.append({target_filepath: code_block.strip()})

    print(f"{len(variations)} variations ont été extraites avec succès.")
    return variations


# --- Agent 3: Test des Variations ---

def run_tests_on_variation(variation: Dict[str, str], original_code: Dict[str, str], config: ConfigParser) -> Dict[str, Any]:
    """
    Exécute la suite de tests sur une variation de code.

    Args:
        variation: Une seule variation de code.
        original_code: Le code original (utilisé pour restaurer les fichiers).
        config: L'objet de configuration.

    Returns:
        Un dictionnaire de résultats contenant le statut du test, le temps d'exécution, etc.
    """
    test_command = config.get('fitness', 'test_command')
    source_dir = config.get('paths', 'source_directory')

    # Sauvegarder la variation dans le répertoire source pour les tests
    for filepath, content in variation.items():
        # Le chemin est absolu, on le rend relatif au répertoire de travail si besoin
        relative_path = os.path.relpath(filepath, start=os.getcwd())
        with open(relative_path, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f"Test de la variation pour {list(variation.keys())[0]}...")
    start_time = time.time()

    result = subprocess.run(test_command, shell=True, capture_output=True, text=True, cwd=source_dir)

    end_time = time.time()
    execution_time = end_time - start_time

    # Restaurer le code original pour ne pas affecter le prochain test
    for filepath, content in original_code.items():
        relative_path = os.path.relpath(filepath, start=os.getcwd())
        with open(relative_path, 'w', encoding='utf-8') as f:
            f.write(content)

    test_passed = result.returncode == 0
    status = "SUCCESS" if test_passed else "FAILURE"
    print(f"Résultat : {status}, Temps d'exécution : {execution_time:.2f}s")

    return {
        "variation": variation,
        "passed": test_passed,
        "execution_time": execution_time,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


# --- Agent 4: Sélection de la Meilleure Variation ---

def select_best_variation(test_results: List[Dict[str, Any]], config: ConfigParser) -> Dict[str, Any]:
    """
    Sélectionne la meilleure variation en fonction des résultats des tests.

    Args:
        test_results: Une liste de dictionnaires de résultats de la fonction de test.
        config: L'objet de configuration.

    Returns:
        La meilleure variation (un dictionnaire de code) ou le code original si aucune n'est meilleure.
    """
    goal = config.get('fitness', 'goal')

    passed_variations = [r for r in test_results if r['passed']]

    if not passed_variations:
        print("Aucune variation n'a réussi les tests. Retour au code original.")
        return None # Indique qu'aucune amélioration n'a été trouvée

    print(f"{len(passed_variations)} variations ont réussi les tests.")

    if goal == 'execution_time':
        # Trier par temps d'exécution croissant
        best_variation_result = min(passed_variations, key=lambda x: x['execution_time'])
        print(f"Meilleure variation trouvée (temps d'exécution le plus bas : {best_variation_result['execution_time']:.2f}s).")
    else: # Par défaut, 'pass_rate'
        # On prend la première qui a réussi
        best_variation_result = passed_variations[0]
        print("Meilleure variation trouvée (première à passer les tests).")

    return best_variation_result['variation']


# --- Agent 5: Écriture des Fichiers de Sortie ---

def write_output_files(initial_code: Dict[str, str], best_code: Dict[str, str], config: ConfigParser):
    """
    Écrit le code amélioré et les rapports dans le répertoire de sortie.
    """
    output_dir = config.get('paths', 'output_directory')

    if not best_code:
        print("Aucun code amélioré à écrire.")
        summary = "# Rapport d'Optimisation\n\nAucune amélioration valide n'a été trouvée après l'analyse."
    else:
        print(f"Écriture du code amélioré dans : {output_dir}")
        for filepath, content in best_code.items():
            # Créer un nom de fichier de sortie sûr
            base_name = os.path.basename(filepath)
            safe_name = "".join(c for c in base_name if c.isalnum() or c in ('.', '_')).rstrip()
            output_path = os.path.join(output_dir, f"improved_{safe_name}")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

        summary = f"""
# Rapport d'Optimisation

Une version améliorée du code a été générée avec succès.

**Fichiers Modifiés :**
- {list(best_code.keys())[0]}

**Résultat :**
Le code amélioré a été sauvegardé dans `{output_dir}`.
"""
        # Génération du fichier diff
        if config.getboolean('reporting', 'generate_diff_file', fallback=False):
            diff_path = os.path.join(output_dir, "improvement.diff")
            # Pour l'instant, on ne gère le diff que pour le premier fichier modifié
            changed_filepath = list(best_code.keys())[0]
            original_content = initial_code.get(changed_filepath, '').splitlines(keepends=True)
            new_content = best_code.get(changed_filepath, '').splitlines(keepends=True)

            diff = difflib.unified_diff(original_content, new_content, fromfile=f"a/{changed_filepath}", tofile=f"b/{changed_filepath}")

            with open(diff_path, 'w', encoding='utf-8') as f:
                f.writelines(diff)
            print(f"Fichier diff sauvegardé dans : {diff_path}")


    if config.getboolean('reporting', 'generate_summary_report', fallback=True):
        report_path = os.path.join(output_dir, "summary_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Rapport de synthèse sauvegardé dans : {report_path}")
