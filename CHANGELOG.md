# Changelog

## 2026-09-24

- Introduced a self-hosted Django + SQLite foundation and kept the showcase UI.
- Added the email-based custom user model, initial migration, health endpoint, focused tests, and CI workflow.
- Added local email/password registration, sign-in, and sign-out with Django hashing, database sessions, CSRF protection, and an accessible styled account flow.
- Added Ruff lint/format checks, JavaScript syntax checking, Django checks, migration validation, and automated tests to CI.
- Added SQLite profile, post, comment, reaction, and follow models with migrations, integrity constraints, indexes, and database-level regression tests.
- Added a signed-in profile editor with server-validated handles and persisted theme/layout settings.
- Added authenticated, paginated post APIs with SQLite-backed comments/reactions, visibility filtering, and owner-only deletion; connected signed-in feed actions to the local server.
- Added owner-only post editing with validation and an edit menu; connected feed actions to look up database-backed posts correctly and load additional pages.
- Added the incremental implementation backlog in `GITHUB_ISSUES.md`.


## Unreleased

- Created the first offline-friendly Meeble showcase shell and seeded social feed.
- Added locally persisted post creation, likes, comments, and hide-post interaction.
- Reworked the home screen around an editorial masthead, clearer feed hierarchy, and an offline palette and illustration system.
- Rounded and strengthened the display typography, lifted key surfaces with layered shadows, and made the feed date and birthday countdown current.
- Added a restrained blurred-color backdrop and glass navigation treatment, replaced the hero statistic tile with the Meeble mascot, softened all-caps labeling, and removed the canned graphic from text-only posts.
- Added initial project, security, development, and architecture documentation.
