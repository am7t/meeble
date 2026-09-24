# Development

## Prerequisites

A modern browser is sufficient. Python 3 is optional if you prefer serving the files locally instead of opening `index.html` directly.

## Run

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000`. The app makes no required network requests and uses system font fallbacks. Browser storage is scoped to the origin; clearing that site’s storage resets the sample.

## Editing

Keep this first slice readable and dependency-free. Use native dialogs and controls where practical, retain keyboard/focus support, and check narrow screens and reduced-motion behavior when changing the UI.

## Planned local-app transition

The agreed next milestone is a local Django server with SQLite. Keep a reproducible dependency manifest, put the SQLite file and private media outside tracked source, use committed migrations, and document an offline-friendly run flow after dependencies have been installed once. Do not add cloud credentials or publicly expose the development server by default.
