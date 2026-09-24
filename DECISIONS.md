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
