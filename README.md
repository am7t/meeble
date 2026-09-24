# Meeble

Meeble is a warm, playful social-platform showcase prototype with an editorial visual identity. The first slice is a responsive home feed with sample stories, original local vector portraits and post artwork, locally saved likes and comments, post creation, and a few UI destinations represented by friendly “coming soon” states.

## Run locally

No package manager, database, account, or network service is required. Open `index.html` in a modern browser, or serve this directory with any static file server, for example:

```sh
python3 -m http.server 8000
```

Then visit `http://localhost:8000`. Feed edits are stored in browser `localStorage` under `meeble.showcase.v1` on that browser profile. Use the browser’s site storage controls to clear the demo and restore the original sample feed.

## Current scope

- Offline static app shell, bespoke art direction, and responsive feed experience.
- Demo profiles, stories, posts, and community sidebar.
- Locally persisted post creation, likes, comments, and hidden posts.
- No backend, real authentication, upload, messaging, marketplace, or remote service integration yet.

See [REQUIREMENTS.md](REQUIREMENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [DEVELOPMENT.md](DEVELOPMENT.md) for the current slice and next steps.
