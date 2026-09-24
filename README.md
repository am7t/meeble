# Meeble

Meeble is a warm, playful social-platform showcase prototype with an editorial visual identity. The first slice is a responsive home feed with sample stories, original local vector portraits and post artwork, locally saved likes and comments, post creation, and a few UI destinations represented by friendly “coming soon” states.

The source lives in the public [am7t/meeble GitHub repository](https://github.com/am7t/meeble). The repository does not host the running demo.

## Run locally

Python 3.10+ is required. The first install needs internet access to download Django; after that, the app itself makes no required external requests.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Then visit `http://127.0.0.1:8000`. The development server binds to this computer only. The SQLite database is `db.sqlite3` and is excluded from Git. The current feed interactions still use browser `localStorage` while the SQLite-backed feature APIs are built incrementally.

## Current scope

- Local Django app shell, SQLite database, bespoke art direction, and responsive feed experience.
- Demo profiles, stories, posts, and community sidebar.
- Locally persisted post creation, likes, comments, and hidden posts.
- Local email/password registration, sign-in, and sign-out use Django password hashing and database-backed sessions.
- Profiles are editable by their signed-in owner, with supported color and layout choices saved in SQLite.
- SQLite has relational profile, post, comment, reaction, and follow tables; the seeded home feed still uses browser storage while feed APIs are built.
- No real Google/Apple sign-in, email delivery, upload, messaging, marketplace, or remote service integration yet.

## Development roadmap

The current development milestone is connecting the existing UI and seeded feed to the local Django application and SQLite schema. It remains self-hosted on the user's own machine. See [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md), and [GITHUB_ISSUES.md](GITHUB_ISSUES.md) for the chosen direction and feature backlog. This does not make the app publicly hosted or add required cloud costs.

See [REQUIREMENTS.md](REQUIREMENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [DEVELOPMENT.md](DEVELOPMENT.md) for the current slice and next steps.
