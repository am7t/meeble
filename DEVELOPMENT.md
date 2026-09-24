# Development

## Prerequisites

Python 3.10 or newer and a modern browser. The first dependency install needs internet access; after installation, the app itself makes no required external requests.

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

Keep modules readable and feature-focused. Use native dialogs and controls where practical, retain keyboard/focus support, and check narrow screens and reduced-motion behavior when changing the UI. Run `python manage.py test` and `python manage.py check` after backend changes.

## Local app

The local Django server and SQLite foundation are in place. Keep a reproducible dependency manifest, put the SQLite file and private media outside tracked source, use committed migrations, and preserve a local-only run command. Do not add cloud credentials or publicly expose the development server by default.
