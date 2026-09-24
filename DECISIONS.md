# Decisions

## D-001: Start with a static local showcase

**Status:** Accepted

**Decision:** Deliver the first slice as dependency-free static HTML, CSS, and JavaScript with fictional seed content and browser-local persistence.

**Reason:** The project goal is an offline prototype suitable for a showcase, without public hosting, paid services, or required setup. Local browser persistence makes the demo feel interactive across launches while keeping it easy to run.

**Tradeoff:** Data stays in one browser profile and is not synchronized, authenticated, or private from that device’s owner. This is not a production backend.

## D-002: Defer social sign-in

**Status:** Accepted for prototype

**Decision:** Do not implement Google/Apple sign-in in the offline showcase.

**Reason:** Federated sign-in requires provider configuration and network access. Simulated sign-in can be considered if an onboarding screen becomes useful to the presentation; real sign-in belongs to a connected product iteration.

## D-003: Use a local Django application with SQLite

**Status:** Accepted

**Decision:** Evolve the showcase into a same-origin Django application using a local SQLite database. Keep the current browser UI and add backend features incrementally. Use Django's built-in authentication, password hashing, sessions, CSRF protections, migrations, and test runner where they fit; write explicit object-level authorization policies for private and user-owned records.

**Reason:** The product should be runnable and demonstrable from one user's machine without public hosting, paid infrastructure, or cloud credentials. SQLite is a real relational database in a single local file; Django supplies mature server-side primitives and keeps the implementation understandable.

**Tradeoffs:** Multiple users on the same local instance share one database and one local server; this does not make a public service. Email delivery, Google/Apple sign-in, payments, and network-based realtime features require external configuration and are deferred. Use Django migrations and keep the database and private media out of Git.
