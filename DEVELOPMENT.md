# Development

## Prerequisites

Python 3.10 or newer and a modern browser. Node.js 22 is only needed for the front-end syntax check. The first dependency install needs internet access; after installation, the app itself makes no required external requests.

## Run

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000`. The SQLite file remains in the project directory and is ignored by Git. Current feed edits remain scoped to browser storage until the feed API milestone is implemented.

## Editing

Keep modules readable and feature-focused. Use native dialogs and controls where practical, retain keyboard/focus support, and check narrow screens and reduced-motion behavior when changing the UI. Install `requirements-dev.txt` for Ruff. Run `ruff check .`, `ruff format --check .`, `node --check web/static/web/app.js`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test` before a change is ready.

## Local app

The local Django server and SQLite schema are in place. Apply committed migrations with `python manage.py migrate`. Authenticated feed routes live under `/api/`; the client sends Django's CSRF token on every mutation. The database enables SQLite foreign keys; migrations add checks, uniqueness rules, and indexes for current domain tables. Keep a reproducible dependency manifest, put the SQLite file and private media outside tracked source, and preserve a local-only run command. Do not add cloud credentials or publicly expose the development server by default.
