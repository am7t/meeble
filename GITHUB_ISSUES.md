# GitHub issue plan

This is the implementation backlog for Meeble in reviewable slices. Issues are tracked in the public [Meeble GitHub repository](https://github.com/am7t/meeble). Keep each change scoped, tested, and documented; split work when a milestone becomes too large for one review.

## Foundation

1. **[Done] Replace the static file server with a local application server**
   - Serve the existing showcase UI and JSON endpoints from one local origin.
   - Keep the application runnable on a developer machine without cloud accounts.
   - Document install, run, backup, and reset behavior.
2. **[Done] Add a SQLite schema and migration workflow**
   - Established normalized accounts, sessions, profiles, posts, comments, reactions, and follows through committed migrations.
   - Enabled foreign keys and added constraints and indexes for the current schema.
   - Kept the database file outside tracked source files. Feature endpoints remain in their own issues.
3. **[Done] Add continuous integration for the local app**
   - Run Ruff formatting and linting, Django checks, migration consistency, and unit/integration tests. Add static type checks if typed modules are introduced.
   - Pin or constrain tool versions and document local equivalents.

## Accounts and profiles

4. **[Done] Implement local email-and-password registration and sign-in**
   - Hash passwords with a maintained password-hashing implementation.
   - Use Django's database-backed sessions, CSRF protection, and password hashing.
   - Validate inputs and return understandable errors without leaking internals. Add rate limiting before any network exposure.
5. **Add account recovery and email-provider boundaries**
   - Design verification and recovery token flows with one-time, expiring tokens.
   - Keep outbound mail behind an adapter; document that delivery needs an email service and is not available in a fully offline run.
6. **[Done] Build editable profiles and validated customization**
   - Store profile fields relationally and supported layout/theme settings as validated structured data.
   - Enforce owner-only edits in the server layer; public profile pages remain future work.
7. **Add in-app Polaroid capture**
   - Capture through the app camera flow only; validate provenance server-side.
   - Keep media private and enforce access checks on delivery.

## Social features

8. **[Done] Move feed posts and reactions to SQLite-backed endpoints**
   - Preserve the seeded showcase feed for first run. Its interactions remain in browser storage as fictional showcase data.
   - Authenticated post creation, editing, deletion, comments, reactions, and paginated database feed reads are in place.
   - Enforce ownership and visibility on every protected operation, including public/follower/private post reads; test owner-only editing and deletion.
9. **[In progress] Add comments, follows, and feed privacy rules**
   - Safe comments and reactions work on SQLite-backed posts. Add follow/unfollow flows and expand feed privacy rules.
   - Cover object-level access boundaries with integration/security tests; base visibility regression coverage is in place.
10. **Add stories and expiration**
    - Support story creation, viewing, deletion, visibility checks, and expiration.
    - Ensure expired stories are excluded from normal API access.
11. **Add short-video feed foundations**
    - Add validated media metadata, paginated delivery, playback controls, and basic engagement.

## Messaging and community

12. **Add conversations and direct messages**
    - Enforce participant authorization for every message and media request.
    - Add read state and safe deletion behavior.
13. **Add group conversations and community membership**
    - Support member management, roles, names, and avatars with server-enforced membership rules.
14. **Add realtime delivery and notifications**
    - Introduce realtime transport only where useful; define reconnect, authorization, and cleanup behavior.
15. **Add voice messages and calling integration boundary**
    - Model media messages and call lifecycle; defer external signaling/relay credentials to local configuration.

## Grail and platform hardening

16. **Add Grail listings, search, and inventory**
    - Implement seller-owned listings, item details, filters, and inventory updates with IDOR coverage.
17. **Add a checkout provider boundary**
    - Validate totals server-side, use idempotent operations, and verify provider webhooks.
    - Do not store card data; document required credentials without asking users to paste secrets into chat.
18. **Add moderation and clearly labeled ad placements**
    - Keep ads separate from organic content and provide reporting/moderation flows.
    - Avoid invasive behavioral tracking.
19. **Complete accessibility, privacy, security, and performance review**
    - Review keyboard access, reduced motion, contrast, private media, authorization, pagination, and query behavior.
20. **Polish release documentation and showcase onboarding**
    - Update screenshots, feature status, setup, limitations, and data backup/reset guidance.

## GitHub setup

The public `am7t/meeble` repository now contains the scoped project history. The app itself remains self-hosted on the user's machine and is not hosted by GitHub Pages. The saved `gh` CLI login is invalid; issue management uses the connected GitHub account until the CLI is re-authenticated.
