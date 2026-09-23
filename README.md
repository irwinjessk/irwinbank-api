# IrwinBank API

API Django REST du projet IrwinBank.

## Prérequis

- Python 3.10 ou plus
- pip
- Docker
- L'image PostgreSQL `postgis/postgis:16-3.4`

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigne ensuite dans `.env` une `SECRET_KEY` propre à l'environnement et le mot de passe PostgreSQL. Ce fichier reste local : il n'est pas versionné.

## Base PostgreSQL

Le projet utilise le conteneur Docker nommé `postgres`, image `postgis/postgis:16-3.4`, port 5432.

Si le conteneur existe déjà :

```bash
docker start postgres
```

S'il n'existe pas :

```bash
docker run --name postgres -d \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=TON_MOT_DE_PASSE \
  -e POSTGRES_DB=irwinbank \
  -p 5432:5432 \
  postgis/postgis:16-3.4
```

Créer la base `irwinbank` si elle n'existe pas encore :

```bash
docker exec postgres psql -U admin -d postgres -c "CREATE DATABASE irwinbank;"
```

## Migrations et serveur

```bash
source venv/bin/activate
python manage.py migrate
python manage.py runserver
```

L'API écoute sur http://127.0.0.1:8000. Les routes métier sont sous `/api/v1/`. Le frontend Vite local (`http://localhost:5173`) est autorisé par `CORS_ORIGIN`.
