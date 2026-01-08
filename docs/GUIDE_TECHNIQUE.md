# Guide Technique Profond : Smart City Traffic Pipeline

Ce document est conçu pour vous donner une maîtrise totale du projet. Si vous lisez et comprenez ce qui suit, vous pourrez expliquer l'architecture complète, chaque choix technologique et le flux de données sans aucune lacune.

---

## 1. Vision d'Ensemble : L’Architecture Lambda (Simplifiée)
Le projet suit un modèle classique du Big Data. On ne se contente pas de stocker des données, on crée un **système à couches** :

1.  **Couche d'Ingestion (Temps Réel)** : Capturer les données sans en perdre une seule.
2.  **Couche de Stockage (Data Lake)** : Garder la vérité brute (Raw Data) pour l'histoire.
3.  **Couche de Traitement (Batch)** : Transformer la bouillie de données en indicateurs intelligents.
4.  **Couche de Service (Serving Layer)** : Rendre les résultats rapides à lire pour l'utilisateur.

---

## 2. Le Rôle de Chaque Composant (Le "Pourquoi")

### 🛰️ Python Generator (Les Capteurs IoT)
*   **Rôle** : Simule les milliers de caméras et capteurs dans la ville.
*   **Pourquoi Python ?** Très simple pour faire du JSON et parler à Kafka.
*   **Concept Clé** : Il génère des données **non-structurées/semi-structurées** (JSON).

### 📥 Apache Kafka (Le Buffer Intelligent)
*   **Pourquoi ne pas envoyer direct dans HDFS ?** 
    - Parce que HDFS n'est pas fait pour recevoir 1000 petits messages par seconde. Il s'épuiserait.
    - Kafka agit comme un **amortisseur**. Il encaisse les pics de trafic. Si HDFS tombe en panne pendant 10 min, Kafka garde les messages en mémoire (Retention).
*   **Terminologie** : Le générateur est un **Producer**, Kafka est le **Broker**.

### 🐘 HDFS (Le Data Lake - Raw Zone)
*   **Rôle** : Stocker des volumes massifs (Terraoctets) à bas coût.
*   **Pourquoi ici ?** On y stocke les données **brutes**. Si on se trompe dans nos calculs Spark demain, on pourra toujours repartir des données brutes stockées ici.
*   **Partitionnement** : On range par `date=YYYY-MM-DD`. C'est vital. Sans ça, pour analyser le trafic d'hier, Spark devrait scanner TOUT le disque depuis le début du projet.

### ⚡ Apache Spark (Le Muscle du Calcul)
*   **Rôle** : C'est le moteur de traitement distribué.
*   **Pourquoi Spark ?** Il est 100x plus rapide qu'Hadoop MapReduce car il travaille en **RAM**.
*   **Transformation** : Il prend le JSON illisible, calcule des moyennes (vitesse moyenne, nombre de voitures) et crée des colonnes propres.

### 🐘 HDFS (Analytics Zone - Parquet)
*   **Pourquoi Parquet ?** 
    - Le JSON est un format "ligne". Le Parquet est un format **"colonnaire"**.
    - Si vous voulez juste la "vitesse moyenne", Spark ne lira que la colonne "vitesse" sur le disque. C'est un gain de performance énorme pour le Big Data.

### 🐘 PostgreSQL (La Serving Layer - LA RÉPONSE À VOTRE QUESTION)
*   **VOTRE QUESTION** : *"Pourquoi Postgres alors qu'on a HDFS ?"*
*   **LA RÉPONSE** : **La Latence**.
    - **HDFS/Spark** sont des outils "Batch". Si vous posez une question à HDFS, il met 10 à 30 secondes à répondre car il doit scanner des fichiers.
    - **PostgreSQL** est une base de données relationnelle indexée. Elle répond en **quelques millisecondes**.
    - **Grafana** a besoin de fluidité. Quand vous changez de filtre sur un dashboard, vous ne voulez pas attendre 30 secondes. On copie donc les *résultats agrégés* de Spark dans Postgres pour que Grafana soit ultra-réactif.
*   **HDFS** = Archives géantes (Big Data).
*   **Postgres** = Tableaux de bord rapides (Fast Data).

### 🛠️ Apache Airflow (Le Chef d'Orchestre)
*   **Rôle** : Il ne traite pas de données. Il dit aux autres QUAND travailler.
*   - "Il est 8h00, Spark, lance le calcul d'hier."
    - "Si Spark échoue, renvoie-moi une alerte."
    - "Vérifie que les données sont bien arrivées dans HDFS avant de commencer."

---

## 3. Le Voyage d'une Donnée (Flux Complet)

1.  **Génération** : Une voiture passe devant le capteur `S1` -> JSON créé.
2.  **Transit** : Le message arrive dans le topic Kafka `traffic-events`.
3.  **Archivage** : Le consumer lit Kafka et écrit le JSON dans `/data/raw/traffic/date=2024...` sur HDFS.
4.  **Réveil** : Airflow sonne l'alarme -> Lance le Job Spark.
5.  **Intelligence** : Spark lit les 10 000 JSON dans HDFS, calcule que la vitesse moyenne est de 42 km/h.
6.  **Publication** : Spark écrit "42 km/h" dans **Postgres**.
7.  **Visualisation** : Grafana interroge Postgres et dessine le point "42" sur le graphique.

---

## 4. Concepts Techniques Avancés (Pour briller en soutenance)

*   **Idempotence** : Le pipeline est conçu pour pouvoir être relancé (en mode "Overwrite" ou "Append") sans corrompre les résultats.
*   **Scalabilité** : Si la ville passe de 10 à 10 000 capteurs, il suffit d'ajouter des "Workers" à Spark et des partitions à Kafka. L'architecture ne change pas.
*   **Consistance** : L'utilisation de Parquet garantit que les schémas de données (noms des colonnes, types) sont respectés et optimisés.
