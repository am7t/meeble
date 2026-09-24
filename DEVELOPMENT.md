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
