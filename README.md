# Alpha-Evolver: Un Outil d'Optimisation de Code Basé sur les LLM

Alpha-Evolver est un framework expérimental conçu pour automatiser l'optimisation de code Python en utilisant des Large Language Models (LLM) et une approche évolutive. Il est piloté par un fichier de configuration unique pour une flexibilité maximale.

## Architecture

Le cœur du système est construit avec **LangGraph**. Il orchestre une série d' "agents" (des fonctions Python) dans un flux de travail cyclique :

1.  **Chargement (`load_code`)**: Le code source est chargé depuis un répertoire.
2.  **Génération (`generate_variations`)**: Le LLM configuré propose plusieurs versions améliorées du code.
3.  **Test (`test_variations`)**: Chaque version est testée en exécutant une commande fournie (la "fonction de fitness"). La réussite et le temps d'exécution sont mesurés.
4.  **Sélection (`select_best`)**: La meilleure variation qui réussit les tests est sélectionnée.
5.  **Boucle**: Si une amélioration est trouvée, elle devient la base pour la prochaine "génération". Le processus se répète.
6.  **Écriture (`write_output`)**: À la fin, le code final et les rapports sont écrits sur le disque.

---

## Structure du Projet

```
.
├── alpha_evolver/      # Code source du framework
│   ├── agents.py       # Logique des nœuds du graphe
│   ├── graph.py        # Assemblage du graphe LangGraph
│   └── llm_provider.py # Fournisseur de clients LLM
├── config/
│   └── config.ini      # LE FICHIER DE CONFIGURATION CENTRAL
├── logs/               # Les fichiers de log sont générés ici
├── output/             # Le code amélioré et les rapports sont générés ici
├── Dockerfile          # Pour construire l'image Docker
├── main.py             # Point d'entrée de l'application
└── requirements.txt    # Dépendances Python
```

---

## Configuration (`config/config.ini`)

C'est le panneau de contrôle de l'application. Vous devez le configurer avant de lancer l'outil.

-   **`[paths]`**: Définissez les chemins pour le code source, les sorties et les logs.
-   **`[llm]`**: Choisissez votre fournisseur (`ollama`, `openai`, etc.) et spécifiez le modèle et les clés API si nécessaire.
-   **`[evolution]`**: Contrôlez le processus évolutif (nombre de générations, nombre de variations à tester).
-   **`[fitness]`**: **La section la plus importante.**
    -   `test_command`: La commande shell à exécuter pour valider une version du code (ex: `pytest`). L'outil s'attend à un code de sortie `0` en cas de succès.
    -   `goal`: Le critère d'optimisation (`pass_rate` ou `execution_time`).
-   **`[reporting]`**: Choisissez les rapports à générer.

---

## Utilisation avec Docker (Méthode Recommandée)

### Étape 1 : Préparer votre environnement

1.  **Code Source**: Placez le code que vous souhaitez optimiser dans un répertoire accessible par Docker (ex: `/root/mon_projet_a_tester`).
2.  **Configuration**: Modifiez `config/config.ini` pour pointer vers ce répertoire et définir votre commande de test.
    ```ini
    [paths]
    source_directory = /root/mon_projet_a_tester

    [fitness]
    test_command = pytest tests/
    ```

### Étape 2 : Construire l'image Docker

À la racine du projet Alpha-Evolver, exécutez :
```bash
docker build -t alpha-evolver .
```

### Étape 3 : Lancer le conteneur

C'est l'étape la plus importante. Vous devez **monter des volumes** pour que le conteneur puisse accéder à votre code et que vous puissiez récupérer les résultats.

```bash
docker run --rm \
  -v /root/mon_projet_a_tester:/root/mon_projet_a_tester \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  alpha-evolver
```

**Explication des volumes (`-v`)** :
-   `-v /root/mon_projet_a_tester:/root/mon_projet_a_tester`: Donne au conteneur l'accès en lecture/écriture à votre projet. **Le chemin avant les deux-points (`:`) doit être le chemin absolu sur votre machine hôte.**
-   `-v $(pwd)/output:/app/output`: Mappe le dossier de sortie du conteneur à un dossier `output` sur votre machine hôte.
-   `-v $(pwd)/logs:/app/logs`: Fait de même pour les logs.

### **NOTE IMPORTANTE SUR L'IMPLÉMENTATION ACTUELLE**

L'agent `generate_code_variations` dans `alpha_evolver/agents.py` contient actuellement une **simulation** de l'appel au LLM. Il ne contacte pas réellement un LLM mais génère des variations factices. Pour une utilisation réelle, vous devrez remplacer la section `--- SIMULATION DE LA SORTIE LLM ---` par un véritable appel `llm_client.invoke(full_prompt)` et une logique pour parser la réponse du modèle.
