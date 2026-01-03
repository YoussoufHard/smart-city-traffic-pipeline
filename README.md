# Smart City Traffic Pipeline

Projet de synthèse Big Data implémentant un pipeline de traitement de données de trafic urbain en temps quasi-réel (Ingestion) et Batch (Traitement).

## Architecture Globale

```mermaid
graph LR
    subgraph "Génération de Données"
        A[Script Python<br/>traffic_generator] -->|JSON Events| B(Kafka Topic<br/>traffic-events)
    end
    
    subgraph "Ingestion & Stockage"
        B -->|Consommateur Python| C[HDFS<br/>/data/raw/traffic]
        C -->|Parquet| HDFS_RAW[Fichiers Raw<br/>(Partitionnés par Date)]
    end
    
    subgraph "Traitement & Analytics"
        HDFS_RAW -->|Lecture Batch| D[Spark Job<br/>traffic_processing.py]
        D -->|Agrégation| E[HDFS<br/>/data/analytics/traffic]
        D -->|JDBC| F[(PostgreSQL<br/>traffic_stats)]
    end
    
    subgraph "Visualisation & Orchestration"
        F -->|Query| G[Grafana Dashboards]
        H[Airflow] -->|Trigger| D
    end

    style A fill:#f9f,stroke:#333
    style B fill:#ffa,stroke:#333
    style C fill:#aff,stroke:#333
    style D fill:#faa,stroke:#333
    style G fill:#9f9,stroke:#333
    style H fill:#99f,stroke:#333
```

---

# Rapport de Projet - Devoir de Synthèse Big Data

Ce rapport détaille les choix techniques et l'implémentation du pipeline de données "Smart City".

## 1. Génération des Données
Le premier maillon de la chaîne est un script Python (`traffic_generator.py`) qui simule des capteurs IoT placés dans différentes zones urbaines.
- **Logique** : Le script génère des événements aléatoires mais réalistes (vitesse, densité) en fonction de l'heure de la journée (pics le matin et le soir).
- **Format** : Les données sont envoyées au format JSON.
- **Outil** : Kafka Producer (`kafka-python`).

> **Capture Recommandée 1** : Montrer le log du terminal exécutant `traffic_generator.py` avec les messages envoyés ("Sent: {...}").
> *(Insérer Capture Ici)*

## 2. Ingestion (Kafka)
Kafka agit comme un tampon (buffer) haute performance pour découpler la production de la consommation.
- **Topic** : `traffic-events`
- **Rôle** : Garantir qu'aucune donnée n'est perdue si le système de stockage est temporairement indisponible.

> **Capture Recommandée 2** : Montrer la commande `kafka-console-consumer` affichant les messages en temps réel dans le topic.
> *(Insérer Capture Ici)*

## 3. Data Lake (HDFS)
Pour le stockage durable, nous utilisons HDFS. Un consommateur dédié (`consumer_to_hdfs.py`) lit les messages Kafka et les écrit dans le Data Lake via WebHDFS.
- **Structure** : `/data/raw/traffic/date=YYYY-MM-DD/`
- **Intérêt** : Cette structure partitionnée permet à Spark de ne lire que les données pertinentes pour une journée donnée.

> **Capture Recommandée 3** : Montrer l'interface Web HDFS (http://localhost:9870) avec les dossiers et fichiers créés.
> *(Insérer Capture Ici)*

## 4. Traitement Distribué (Spark)
Le cœur du traitement est assuré par Apache Spark (PySpark).
- **Transformation** : Le job lit les fichiers JSON bruts depuis HDFS.
- **Métriques** :
  - Vitesse moyenne par capteur.
  - Détection de congestion (Vitesse < 30 km/h).
- **Optimisation** : Utilisation de la DataFrame API pour des performances optimales.

> **Capture Recommandée 4** : Montrer le terminal Airflow ou Spark Master indiquant que le job a réussi (Status: SUCCEEDED).
> *(Insérer Capture Ici)*

## 5. Analytics & Stockage (Parquet/PostgreSQL)
Les résultats agrégés sont stockés à deux endroits :
1. **HDFS (Parquet)** : Pour de l'analyse long terme (OLAP). Le format Parquet est colonnaire et compressé, idéal pour le Big Data.
2. **PostgreSQL** : Pour servir les tableaux de bord en temps réel (OLTP/Serving Layer).

> **Capture Recommandée 5** : Montrer une requête SQL simple dans Postgres (`SELECT * FROM traffic_stats LIMIT 5;`) prouvant que les données sont bien là.
> *(Insérer Capture Ici)*

## 6. Visualisation (Grafana)
Grafana se connecte à PostgreSQL pour afficher les KPIs.
- **Dashboards** : Courbes de vitesse moyenne, alertes de congestion.

> **Capture Recommandée 6** : Capture d'écran du Dashboard Grafana final avec les graphiques.
> *(Insérer Capture Ici)*

## 7. Orchestration (Airflow)
Airflow planifie et surveille l'exécution du pipeline.
- **DAG** : `traffic_pipeline` s'exécute toutes les 5 minutes.
- **Avantage** : En cas d'échec, Airflow peut relancer le job automatiquement.

> **Capture Recommandée 7** : Capture de l'interface Airflow montrant le DAG en vert (Graph View ou Grid View).
> *(Insérer Capture Ici)*

---

# Manuel d'Utilisation

## Prérequis
- Docker Desktop
- Python 3+

## Lancement
1. Démarrer l'infrastructure :
   ```bash
   docker-compose up -d --build
   ```

2. Vérifier que les services tournent :
   - Kafka : `localhost:9092`
   - HDFS WebUI : `http://localhost:9870`
   - Spark Master : `http://localhost:8080`
   - Airflow : `http://localhost:8081` (User/Pass: admin/admin)
   - Grafana : `http://localhost:3000` (User/Pass: admin/admin)

3. Le pipeline est automatique :
   - Le générateur (`traffic-generator`) commence à émettre des données immédiatement.
   - Le consommateur (`hdfs-consumer`) les archive dans HDFS.
   - Airflow lance le job Spark toutes les 5 minutes (via le DAG `traffic_pipeline`).

## Structure du Projet
```
.
├── airflow/            # DAGs Airflow
├── data-generator/     # Script de simulation de trafic
├── kafka/              # Scripts de consommation Kafka -> HDFS
├── spark/              # Job Spark de traitement
├── grafana/           # Dashboards (JSON)
├── docs/               # Documentation détaillée
└── docker-compose.yml  # Infrastructure complète
```
