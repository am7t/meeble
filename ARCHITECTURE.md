# Architecture

## Current local application foundation

Django serves the current UI from `web/templates/web/index.html` and its CSS, JavaScript, and local SVG assets from `web/static/web/`. Run it on `127.0.0.1` only. SQLite is configured in `meeble_site/settings.py`; `accounts.User` is the custom email-identified user model and has a tracked migration. Account screens provide local registration, email verification, sign-in, POST-only sign-out, and expiring one-use password recovery. The email backend defaults to Django's console backend, so verification and reset links are printed locally and no mail service is required; deployments can select another backend through environment settings. Verification uses a separate timestamped token, stays pending until the user confirms via a CSRF-protected POST, and expires according to `PASSWORD_RESET_TIMEOUT`. New accounts receive a relational profile, and signed-in users can edit only their own profile and validated theme/layout choices. Django owns password hashing, database-backed session middleware, and CSRF protection. Relational profile, post, comment, reaction, follow, and story tables are present. Signed-in users can read a paginated database feed and create, edit, and delete their own posts; comments and reactions are stored in SQLite and checked against post visibility. Follow actions are authenticated and exclude self-following; the paginated people directory returns only public profile fields. Public profile pages show public identity fields and server-filter posts by viewer visibility. The Following filter returns public and follower-visible posts from accounts followed by the current user. Stories expire after 24 hours, use public/follower/private visibility, and store sanitized JPEGs under the ignored private-media directory. An authenticated view checks visibility before streaming each image; `purge_expired_stories` removes expired rows and their files. The fictional sample feed stays in the browser as showcase data, and its interactions continue to use versioned `localStorage`.

The UI writes only after a user action. Storage errors are handled with a readable message, and user-entered text is HTML-escaped before feed rendering. The local database file is excluded from Git.

## Chosen application foundation

The app is a self-hosted local app that runs on the user's own machine. It keeps the current HTML/CSS/JavaScript experience behind a same-origin Django application with SQLite. Django provides the authentication, password hashing, session, CSRF, ORM, migration, and test facilities without a paid service. Use small Django apps/modules around cohesive features; do not introduce a separate frontend build stack until it solves a concrete need.

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

Profile, post, comment, reaction, and follow tables have initial constraints and indexes. The profile editor writes the signed-in user's own record through a server-side form. Feed endpoints bind writes to the signed-in user and enforce post visibility and ownership server-side. Public profile pages use the same follower/public visibility rules; email and authentication fields stay out of profile output.
