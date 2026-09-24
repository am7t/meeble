# GitHub issue plan

This is the initial backlog for building Meeble in reviewable slices. Issues should be opened in the Meeble GitHub repository once the repository exists and is connected. Keep each change scoped, tested, and documented; split work when a milestone becomes too large for one review.

## Foundation

1. **Replace the static file server with a local application server**
   - Serve the existing showcase UI and JSON endpoints from one local origin.
   - Keep the application runnable on a developer machine without cloud accounts.
   - Document install, run, backup, and reset behavior.
2. **Add a SQLite schema and migration workflow**
   - Establish normalized accounts, sessions, profiles, posts, comments, reactions, and follows.
   - Enable foreign keys and add constraints and indexes where needed.
   - Keep the database file outside tracked source files.
3. **Add continuous integration for the local app**
   - Run formatting, linting, type checks where applicable, unit and integration tests, and a build/smoke check.
   - Pin or constrain tool versions and document local equivalents.

## Accounts and profiles

4. **Implement local email-and-password registration and sign-in**
   - Hash passwords with a maintained password-hashing implementation.
   - Use expiring, revocable server-side sessions and secure cookie settings.
   - Validate inputs and return understandable errors without leaking internals.
5. **Add account recovery and email-provider boundaries**
   - Design verification and recovery token flows with one-time, expiring tokens.
   - Keep outbound mail behind an adapter; document that delivery needs an email service and is not available in a fully offline run.
6. **Build editable profiles and validated customization**
   - Store profile fields relationally and supported layout/theme settings as validated structured data.
   - Enforce owner-only edits in the server layer.
7. **Add in-app Polaroid capture**
   - Capture through the app camera flow only; validate provenance server-side.
   - Keep media private and enforce access checks on delivery.

## Social features

8. **Move feed posts and reactions to SQLite-backed endpoints**
   - Preserve the seeded showcase feed for first run.
   - Add authenticated create, edit, delete, like, and pagination flows.
   - Enforce ownership and visibility on every protected operation.
9. **Add comments, follows, and feed privacy rules**
   - Support safe text, reactions, and follow relationships.
   - Cover object-level access boundaries with integration/security tests.
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

The project currently has local Git history but no configured remote. The GitHub connector is available, while the saved `gh` CLI login is invalid. Select or create the intended Meeble repository before opening these issues or pushing commits.
