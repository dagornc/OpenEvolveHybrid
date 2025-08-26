import configparser
import logging
import os
import time
from alpha_evolver.graph import create_graph
from alpha_evolver.llm_provider import get_llm_provider

def setup_logging(log_dir: str):
    """Configure la journalisation pour la console et un fichier."""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = f"alpha_evolver_{time.strftime('%Y%m%d-%H%M%S')}.log"
    log_filepath = os.path.join(log_dir, log_filename)

    # Créer un logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Créer un formateur
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler pour le fichier
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logging.info(f"Journalisation configurée. Fichier de log : {log_filepath}")


def main():
    """
    Point d'entrée principal de l'application Alpha-Evolver.
    """
    print("=========================================")
    print("=== Démarrage d'Alpha-Evolver ===")
    print("=========================================")

    try:
        # --- 1. Charger la configuration ---
        config_path = 'config/config.ini'
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Fichier de configuration non trouvé à l'emplacement : {config_path}")

        config = configparser.ConfigParser()
        config.read(config_path)

        # --- 2. Configurer la journalisation ---
        log_dir = config.get('paths', 'log_directory', fallback='logs')
        setup_logging(log_dir)

        logging.info("Configuration chargée avec succès.")

        # --- 3. Initialiser le client LLM et le graphe ---
        llm_client = get_llm_provider(config)
        app = create_graph()
        logging.info("Graphe d'exécution créé.")

        # --- 4. Définir l'état initial ---
        # L'état initial est un dictionnaire qui correspond à la structure de GraphState
        initial_state = {
            "config": config,
            "llm_client": llm_client,
            "current_generation": 1,
            "max_generations": config.getint('evolution', 'generations', fallback=5)
        }
        logging.info(f"État initial préparé. Début de l'évolution pour {initial_state['max_generations']} générations.")

        # --- 5. Invoquer le graphe ---
        # Utiliser .stream() pour voir les événements en temps réel
        for event in app.stream(initial_state):
            for node, output in event.items():
                logging.info(f"--- Fin du Nœud: {node} ---")
                # logging.debug(f"Sortie du nœud : {output}") # Utile pour le débogage

        logging.info("Processus d'évolution terminé.")

    except FileNotFoundError as e:
        logging.error(f"Erreur de Fichier : {e}")
    except KeyError as e:
        logging.error(f"Erreur de Configuration : Clé manquante dans config.ini - {e}")
    except Exception as e:
        logging.error(f"Une erreur inattendue est survenue : {e}", exc_info=True)

    print("=========================================")
    print("=== Alpha-Evolver a terminé son exécution. ===")
    print("=========================================")


if __name__ == "__main__":
    main()
