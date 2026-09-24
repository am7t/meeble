# Contributor notes

- Keep the current prototype dependency-free and runnable as static files unless the product direction changes.
- Keep markup, presentation, and behavior in `index.html`, `styles.css`, and `app.js`; split files when a feature makes one hard to follow.
- Use semantic controls, visible focus states, accessible labels, responsive layouts, and reduced-motion support.
- Escape every user-provided value before inserting it into HTML. Treat browser storage as untrusted input and keep authorization claims out of client-only code.
- Persist only showcase data in browser storage. Never put credentials, private data, or real user information in the demo seed.
- Keep docs aligned with working behavior; mark planned and simulated features clearly.
- When a backend is introduced, add relational migrations and make every protected resource enforce authorization server-side.
