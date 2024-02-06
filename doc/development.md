# Development

```sh
python3 -m venv env && source env/bin/activate
(env) pip install -r requirements.txt
```

## Docker

### Compose (including dependencies)

Running at [http://127.0.0.1:5002]
Celery Flower at [http://127.0.0.1:5557]

```sh
docker-compose up --build
```

## Database

```sh
flask db init
flask db migrate
flask db upgrade
```

## i18n

<https://python-babel.github.io/flask-babel/>

### Init

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot . && pybabel init -i messages.pot -d project/translations -l de
```

### Add locale

```sh
pybabel init -i messages.pot -d project/translations -l en
```

### Extract new msgid's and merge into \*.po files

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot . && pybabel update -N -i messages.pot -d project/translations
```

#### Compile after translation is done

```sh
pybabel compile -d project/translations
```

## Celery

```sh
dotenv run celery -A project.celery purge
```
