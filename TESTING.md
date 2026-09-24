# Testing strategy

The project uses Django's test runner with a separate test database and CI. Current tests cover account/password/session/CSRF behavior, owner-only profile editing, escaped profile text, migration backfills, relational constraints, feed pagination, visibility filtering, authenticated mutations, and denied cross-owner post editing/deletion. Add focused security regression tests for denied access as well as successful cases. Browser-level end-to-end tooling can be added as the server-backed UI stabilizes.
