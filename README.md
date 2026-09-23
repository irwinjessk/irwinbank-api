# IrwinBank API

API Django du projet IrwinBank.

## Prérequis

- Python 3.10 ou plus
- Docker, avec le conteneur PostgreSQL `postgis/postgis:16-3.4` déjà lancé sur le port 5432

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigne `SECRET_KEY` et le mot de passe PostgreSQL dans `.env`.

La base s'appelle `irwinbank`. Elle vit dans le conteneur PostGIS déjà utilisé en local, pas dans un second serveur.

```bash
docker exec postgres psql -U admin -d postgres -c "CREATE DATABASE irwinbank;"
python manage.py migrate
python manage.py runserver
```

L'API écoute sur http://127.0.0.1:8000. Le frontend local est autorisé depuis http://localhost:5173.
