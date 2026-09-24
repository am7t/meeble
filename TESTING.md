# Testing strategy

The current static showcase has no automated test runner or CI configuration. The next foundation introduces Django's test runner and a separate test database. Add tests alongside each feature: safe text rendering, database constraints, authentication/session behavior, ownership checks, media access, and core feed flows. Add focused security regression tests for denied access as well as successful cases. Browser-level end-to-end tooling can be added when the local app has stable server-backed flows; avoid adding it before then.
