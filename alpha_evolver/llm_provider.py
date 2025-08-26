import os
from configparser import ConfigParser

# Importer les classes LLM nécessaires depuis LangChain
from langchain_community.llms.ollama import Ollama
from langchain_openai import OpenAI

# Note: Les autres fournisseurs comme OpenRouter ou HuggingFace peuvent être ajoutés ici.
# from langchain_community.llms.huggingface_endpoint import HuggingFaceEndpoint
# from langchain_community.llms.openrouter import OpenRouter


def get_llm_provider(config: ConfigParser):
    """
    Lit la configuration et retourne une instance du client LLM approprié.

    Cette fonction agit comme une "factory" qui choisit le bon fournisseur de LLM
    (Ollama, OpenAI, etc.) en fonction du fichier de configuration et l'initialise
    avec les bons paramètres (modèle, URL, clé API, etc.).

    Args:
        config: Un objet ConfigParser chargé avec le fichier config.ini.

    Returns:
        Une instance d'un client LLM compatible avec LangChain.

    Raises:
        ValueError: Si le fournisseur spécifié dans la config n'est pas supporté.
    """
    llm_config = config['llm']
    provider = llm_config.get('provider')

    print(f"Initialisation du fournisseur LLM : {provider}")

    if provider == 'ollama':
        return Ollama(
            base_url=llm_config.get('ollama_base_url'),
            model=llm_config.get('ollama_model'),
            temperature=llm_config.getfloat('temperature')
        )

    elif provider == 'openai':
        # La clé API peut être dans la config ou dans les variables d'environnement
        api_key = llm_config.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Clé API OpenAI non trouvée. Veuillez la définir dans config.ini ou dans la variable d'environnement OPENAI_API_KEY.")

        return OpenAI(
            model_name=llm_config.get('openai_model'),
            openai_api_key=api_key,
            temperature=llm_config.getfloat('temperature'),
            max_tokens=llm_config.getint('max_tokens')
        )

    elif provider == 'openrouter':
        raise NotImplementedError("Le fournisseur OpenRouter est prévu mais pas encore implémenté.")

    elif provider == 'huggingface':
        raise NotImplementedError("Le fournisseur HuggingFace est prévu mais pas encore implémenté.")

    else:
        raise ValueError(f"Fournisseur LLM non supporté : '{provider}'. Les options valides sont 'ollama', 'openai', 'openrouter', 'huggingface'.")
