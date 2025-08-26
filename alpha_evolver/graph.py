from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from configparser import ConfigParser

# Importer les fonctions des agents que nous avons définies
from .agents import (
    load_code_from_disk,
    generate_code_variations,
    run_tests_on_variation,
    select_best_variation,
    write_output_files
)
# Importer le fournisseur de LLM
from .llm_provider import get_llm_provider


# --- 1. Définition de l'État du Graphe ---
# L'état est un dictionnaire qui circule entre les nœuds du graphe.
# Chaque nœud peut lire et écrire dans cet état.

class GraphState(TypedDict):
    config: ConfigParser
    llm_client: Any
    initial_code: Dict[str, str]  # Le code du tout début, ne change jamais
    original_code: Dict[str, str] # Le code de base pour la génération actuelle
    variations: List[Dict[str, str]]
    test_results: List[Dict[str, Any]]
    best_variation: Dict[str, str]
    current_generation: int
    max_generations: int


# --- 2. Fonctions des Nœuds ---
# Ce sont des "wrappers" autour de nos agents pour les rendre compatibles
# avec la signature attendue par LangGraph (qui prend un état et retourne
# un dictionnaire pour mettre à jour cet état).

def load_code_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- Nœud: Chargement du Code ---")
    config = state['config']
    original_code = load_code_from_disk(config)
    # On sauvegarde le code initial et on définit le code de travail
    return {"initial_code": original_code, "original_code": original_code}

def generate_variations_node(state: GraphState) -> Dict[str, Any]:
    print(f"\n--- Nœud: Génération (Génération {state['current_generation']}) ---")
    variations = generate_code_variations(
        state['original_code'], state['llm_client'], state['config']
    )
    return {"variations": variations}

def test_variations_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- Nœud: Test des Variations ---")
    results = []
    # Note: Dans une implémentation avancée, on pourrait paralléliser ces tests.
    for variation in state['variations']:
        result = run_tests_on_variation(variation, state['original_code'], state['config'])
        results.append(result)
    return {"test_results": results}

def select_best_variation_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- Nœud: Sélection de la Meilleure Variation ---")
    best_variation = select_best_variation(state['test_results'], state['config'])
    # Si une meilleure variation est trouvée, elle devient le nouveau "code original"
    # pour la prochaine génération.
    if best_variation:
        return {"best_variation": best_variation, "original_code": best_variation}
    return {"best_variation": None}

def write_output_node(state: GraphState) -> Dict[str, Any]:
    print("\n--- Nœud: Écriture des Fichiers de Sortie ---")
    # On passe maintenant le code initial au nœud d'écriture pour le diff
    write_output_files(
        initial_code=state['initial_code'],
        best_code=state['best_variation'],
        config=state['config']
    )
    return {}

def increment_generation_node(state: GraphState) -> Dict[str, Any]:
    """Incrémente le compteur de génération."""
    current_gen = state['current_generation']
    next_gen = current_gen + 1
    print(f"\n--- Nœud: Passage à la génération {next_gen} ---")
    return {"current_generation": next_gen}


# --- 3. Logique Conditionnelle (Arêtes) ---

def should_continue_evolution(state: GraphState) -> str:
    """
    Détermine si le graphe doit continuer vers une nouvelle génération
    ou terminer le processus.
    """
    print("\n--- Condition: Continuer l'évolution ? ---")
    current_gen = state['current_generation']
    max_gen = state['max_generations']

    # La vérification se fait avant l'incrémentation de la prochaine génération
    if current_gen > max_gen:
        print("Nombre maximum de générations atteint. Fin du processus.")
        return "end"
    else:
        print(f"Prêt pour la génération {current_gen}/{max_gen}. Continuation...")
        return "continue"

# --- 4. Assemblage du Graphe ---

def create_graph():
    """
    Crée et compile le graphe LangGraph.
    Cette fonction ne prend plus d'arguments car la configuration et le client
    seront dans l'état passé lors de l'invocation.
    """
    # Créer une instance du StateGraph
    workflow = StateGraph(GraphState)

    # Ajouter les nœuds
    workflow.add_node("load_code", load_code_node)
    workflow.add_node("generate_variations", generate_variations_node)
    workflow.add_node("test_variations", test_variations_node)
    workflow.add_node("select_best", select_best_variation_node)
    workflow.add_node("increment_generation", increment_generation_node) # Nouveau nœud
    workflow.add_node("write_output", write_output_node)

    # Définir le point d'entrée
    workflow.set_entry_point("load_code")

    # Définir les arêtes (le flux de travail)
    workflow.add_edge("load_code", "generate_variations")
    workflow.add_edge("generate_variations", "test_variations")
    workflow.add_edge("test_variations", "select_best")
    workflow.add_edge("select_best", "increment_generation") # Le flux passe par l'incrémentation

    # Ajouter l'arête conditionnelle pour la boucle d'évolution
    workflow.add_conditional_edges(
        "increment_generation", # La condition est maintenant après l'incrémentation
        should_continue_evolution,
        {
            "continue": "generate_variations", # Boucler pour une nouvelle génération
            "end": "write_output"             # Terminer et écrire les résultats
        }
    )
    workflow.add_edge("write_output", END)

    # Compiler le graphe en un objet exécutable
    app = workflow.compile()

    print("Graphe compilé avec succès.")
    return app
