
# SysWatch-API

## 1. Présentation du projet

SysWatch-API est une solution de supervision système développée en Python permettant de collecter, analyser, stocker et visualiser les métriques d'un ordinateur en temps réel.

Les données sont enregistrées dans une base SQLite et visualisées à travers un tableau de bord Grafana.

## 2. Fonctionnalités

- Supervision du processeur (CPU).
- Surveillance de la mémoire vive (RAM).
- Surveillance de l'espace disque.
- Mesure des opérations de lecture et d'écriture (IOPS).
- Supervision des processus.
- Vérification des services HTTP et TCP.
- Surveillance de l'expiration des certificats SSL.
- Détection automatique des dépassements de seuils.
- Détection de croissance anormale de la mémoire.
- Calcul du taux de disponibilité des services (SLA).
- Journalisation des événements et incidents.
- Rétention automatique des données.

## 3. Technologies utilisées

- Python
- Psutil
- SQLite
- Grafana
- JSON
- Git

## 4. Architecture du projet

    SysWatch-API/
    ├── src/
    │   ├── main.py
    │   ├── collector.py
    │   ├── process_monitor.py
    │   ├── database.py
    │   ├── healthcheck.py
    │   ├── alerts.py
    │   ├── config.py
    │   └── logger.py
    ├── data/
    ├── grafana/
    ├── docs/
    ├── tests/
    ├── logs/
    ├── config.json
    ├── requirements.txt
    └── README.md

## 5. Installation

Créer un environnement virtuel Python :

    python -m venv .venv

Activer l'environnement virtuel sous Windows :

    .\.venv\Scripts\Activate.ps1

Installer les dépendances :

    pip install -r requirements.txt

## 6. Lancement du programme

Depuis la racine du projet :

    python -m src.main

La collecte des métriques est effectuée toutes les cinq secondes selon la configuration actuelle.

Les données sont enregistrées dans :

    data/syswatch.db

## 7. Configuration

Le fichier config.json permet de personnaliser les paramètres de supervision.

Seuils configurés par défaut :

| Métrique | Seuil |
|---|---|
| CPU | 90 % |
| RAM | 90 % |
| Disque | 85 % |
| Expiration SSL | 15 jours |
| Rétention des données | 7 jours |

## 8. Dashboard Grafana

Installer Grafana ainsi que le plugin SQLite Data Source (frser-sqlite-datasource).

Configurer la source de données avec le chemin absolu du fichier data/syswatch.db.

Importer ensuite le fichier JSON disponible dans le dossier grafana et sélectionner la source SQLite correspondante.

Le dashboard contient huit panels :

1. Utilisation CPU
2. Utilisation RAM
3. Utilisation disque
4. Activité disque (IOPS)
5. Supervision des processus
6. Disponibilité des services
7. SLA
8. Journal des incidents

### Aperçu du dashboard

![Dashboard 1](grafana/Dashboard%201.png)

![Dashboard 2](grafana/Dashboard%202.png)

## 9. Base de données

La base SQLite contient cinq tables principales :

- host_metrics
- disk_partitions
- process_metrics
- service_health
- system_incidents

## 10. Conclusion

SysWatch-API permet de centraliser la supervision des ressources système, de surveiller la disponibilité des services et de détecter automatiquement les anomalies grâce à une architecture modulaire.

## 11. Auteur

Sabri DAHMANI

Projet réalisé dans le cadre d'une évaluation Python.

Novembre 2026.