# Testing strategy

The project uses Django's test runner with a separate test database and CI. Current tests cover account/password/session/CSRF behavior, owner-only profile editing, escaped profile text, migration backfills, and relational constraints for profiles, posts, comments, reactions, and follows. Add tests alongside each feature: media access and core feed flows. Add focused security regression tests for denied access as well as successful cases. Browser-level end-to-end tooling can be added when the local app has stable server-backed flows; avoid adding it before then.
