# Architecture

## Current prototype

The first iteration is a static browser application: `index.html` owns semantic page structure, `styles.css` owns the visual system and responsive behavior, `app.js` renders seeded feed data and handles interactions, and `assets/` contains local SVG portraits and editorial illustrations. A small versioned `localStorage` record preserves showcase edits. There is no server, database, identity provider, payment provider, or remote media storage.

The seed gives a new browser a ready-made feed. The app only writes after a user action. Storage errors are handled with a readable message, and user-entered text is HTML-escaped before feed rendering.

## Next foundation: a local SQLite application

The agreed direction is a self-hosted local app that runs on the user's own machine. It will keep the current HTML/CSS/JavaScript experience and put it behind a same-origin Django application with SQLite. Django is a good fit here because its authentication, password hashing, session, CSRF, ORM, migration, and test facilities cover foundational needs without a paid service. Use small Django apps/modules around cohesive features; do not introduce a separate frontend build stack until it solves a concrete need.

The database is a local file excluded from Git. Use normal relational tables for accounts, profiles, posts, comments, reactions, follows, messages, listings, and orders; reserve validated structured configuration for profile customization. Use migrations for every schema change. Keep media on local storage initially, outside public static assets, and gate private delivery in application views.

Provider sign-in, email delivery, real-time calling, and payments need network services and credentials. They are not part of an offline-only run. Integrate them later behind small adapters if the product direction changes. The browser is never an authorization boundary; every operation on user-owned or private data must check ownership and visibility on the server.

## Initial domain model

- **User**: email, password hash, account state, and timestamps; Django authentication primitives with a custom user model established before the first migration.
- **Profile**: one-to-one with User; public display fields and validated customization configuration.
- **Follow**: directed relationship between two users, unique per pair.
- **Post**: author, caption, visibility, media references, and timestamps.
- **Reaction**: user and post, unique per pair (expand reaction type only when the product needs it).
- **Comment**: author, post, safe plain-text body, and timestamps.
- **Story**: author, private media reference, visibility, creation time, and expiration time.
- **Conversation / Membership / Message**: normalized membership and message records; fetch paths must enforce membership.
- **Listing / Order / OrderItem**: seller-owned inventory and immutable purchase snapshots; external payment state remains behind an adapter.
- **MediaAsset**: owner, storage key, validated type/size, visibility, and provenance metadata where required.

Add indexes and database constraints with the feature that needs them. Add later domain tables only when implementing their feature rather than anticipating every idea now.
