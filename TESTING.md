# Testing strategy

The current slice has no automated test runner or CI configuration. Its data and rendering are intentionally small enough to review directly. Before adding a framework, choose tests that protect real behavior: safe text rendering, storage migration/error handling, feed interactions, and responsive end-to-end showcase flows. Authentication, ownership, private media, and payment security tests belong with their respective backend features.
