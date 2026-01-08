# Fonctionnement Interne & Vérification du Pipeline

Ce document est une "Fiche Mémo" pour comprendre ce qui se passe sous le capot et comment vérifier que tout fonctionne.

---

## 1. Comment savoir si ça marche ? (La Check-list)

Si vous voyez ces 4 choses, c'est que le pipeline tourne parfaitement.

### ✅ Étape 1 : Le cœur bat-il ? (Générateur)
Le script `traffic-generator` doit "cracher" des logs en continu. C'est le pouls du système.
**Commande à lancer :**
```bash
docker logs -f traffic-generator
```
**Ce que vous devez voir :**
Des lignes qui défilent avec "Sent event to Kafka...".
> *Si ça défile, c'est que les données sont créées et envoyées à Kafka.*

### ✅ Étape 2 : Les données arrivent-elles ? (HDFS)
Le `hdfs-consumer` doit prendre ces messages et les écrire sur le disque.
**Vérification Visuelle :**
1. Allez sur **[http://localhost:9870](http://localhost:9870)** (Interface HDFS).
2. Cliquez sur **Utilities** -> **Browse the file system**.
3. Naviguez dans : `/data/raw/traffic/`.
**Ce que vous devez voir :**
Un dossier avec la date d'aujourd'hui (ex: `date=2024-01-04`). Cliquez dessus, vous devriez voir des fichiers `.json` s'accumuler.

### ✅ Étape 3 : Le traitement se lance-t-il ? (Airflow)
Airflow doit déclencher le calcul toutes les 5 minutes.
**Vérification Visuelle :**
1. Allez sur **[http://localhost:8081](http://localhost:8081)** (Login: `admin`/`admin`).
2. Cherchez le DAG `traffic_pipeline`.
3. Vérifiez que le bouton "On/Off" à gauche est sur **ON** (Bleu).
4. Regardez la grille à droite : vous devriez voir des carrés **Verts foncé** (Succès).

### ✅ Étape 4 : Le résultat est-il là ? (Grafana)
Grafana affiche le résultat final.
**Vérification Visuelle :**
1. Allez sur **[http://localhost:3000](http://localhost:3000)**.
2. Ouvrez le dashboard (s'il est configuré) ou explorez les données.
3. Si les graphiques bougent, c'est gagné.

---

## 2. Le Fonctionnement "Sous le capot"

Imaginez une usine de tri postal.

### Phase 1 : La Boîte aux Lettres (Kafka)
- Les capteurs (le script Python) postent des lettres (données JSON) dans une boîte géante appelée **Kafka**.
- Ils ne savent pas ce qui va se passer après, ils postent juste très vite.
- Kafka garde les lettres en sécurité.

### Phase 2 : L'Archiviste (HDFS Consumer)
- Un employé (le script `consumer_to_hdfs.py`) vide la boîte Kafka en continu.
- Il met toutes les lettres dans des cartons d'archives **HDFS**.
- Il classe les cartons par **DATE** (un carton par jour).
- *Pourquoi ?* Pour ne pas perdre une miette de donnée brute.

### Phase 3 : L'Analyste (Spark)
- Toutes les 5 minutes, le chef (Airflow) réveille l'analyste (Spark).
- L'analyste ouvre les cartons d'archives récents.
- Il lit tout, calcule la vitesse moyenne, repère les embouteillages.
- Il écrit son rapport propre dans deux endroits :
    1. **Parquet** (Pour l'archivage long terme optimisé).
    2. **Postgres** (Pour l'affichage immédiat sur les écrans).

### Phase 4 : L'Écran de Contrôle (Grafana)
- Grafana lit simplement le rapport dans Postgres et dessine les courbes.
