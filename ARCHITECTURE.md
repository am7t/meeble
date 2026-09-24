# Architecture

## Current prototype

The first iteration is a static browser application: `index.html` owns semantic page structure, `styles.css` owns the visual system and responsive behavior, and `app.js` renders seeded feed data and handles interactions. A small versioned `localStorage` record preserves showcase edits. There is no server, database, identity provider, payment provider, or remote media storage.

The seed gives a new browser a ready-made feed. The app only writes after a user action. Storage errors are handled with a readable message, and user-entered text is HTML-escaped before feed rendering.

## Direction as the project grows

Keep the showcase slice small. If real multi-user behavior is added, move persistence and security-sensitive rules to a relational backend. Add feature modules as needed and put external email, payment, media, and storage integrations behind focused interfaces. The client’s local data is never an authorization boundary.
