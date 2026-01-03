# Architecture & Choix Techniques

## Vue d'ensemble
L'architecture est conçue pour être robuste ("Solid") et évolutive, séparant clairement les responsabilités (Ingestion vs Traitement).

Diagramme : 
`Generator -> Kafka -> Consumer -> HDFS (Raw) -> Spark (Batch) -> Analytics (Parquet/SQL) -> Grafana`

## Justifications Techniques

### 1. Kafka (Message Broker)
**Pourquoi ?**
- Découplage : Le générateur ne dépend pas de la vitesse d'écriture dans HDFS.
- Streaming : Permet de passer à une architecture Lambda ou Kappa pure si besoin.
- Rétention : Kafka garde les événements si le consommateur HDFS tombe.

### 2. HDFS (Data Lake)
**Pourquoi ?**
- Stockage "Raw" : On stocke la donnée brute sans transformation (Single Source of Truth).
- Partitionnement : `/data/raw/traffic/date=YYYY-MM-DD/` permet de charger facilement les données d'une période spécifique.

### 3. Spark (Processing)
**Pourquoi ?**
- Puissance de calcul distribué pour agréger des millions d'événements.
- Facilité d'écriture en code (PySpark) vs SQL complexe.
- **Détails du Job** :
    - Calcul de la vitesse moyenne par capteur.
    - Détection de congestion (`speed < 30 km/h`).
    - Écriture en mode `Append`.

### 4. Parquet (Format de Sortie)
**Pourquoi ?**
- **Stockage Colonnaire** : Très performant pour l'analytique (lire seulement les colonnes nécessaires comme `speed`).
- **Compression** : Réduit l'espace disque (Snappy/Gzip).
- **Schema** : Conserve le type des données (contrairement au CSV/JSON).

### 5. Airflow (Orchestration)
**Pourquoi ?**
- Planification fiable des jobs Spark.
- Gestion des dépendances (Retry mechanism, Alerting).

## KPIs (Indicateurs Clés de Performance)
Les métriques calculées et visualisées sont :
- **Trafic Moyen** : Nombre de véhicules par minute.
- **Vitesse Moyenne** : Fluidité du trafic.
- **Congestion** : Indicateur binaire (Status: FLUID / CONGESTION).
