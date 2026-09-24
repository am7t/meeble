# Security notes

The current release is a local, single-browser showcase with fictional sample data. It has no accounts, server endpoints, secrets, uploads, or payment processing. Browser storage is editable by the browser owner and must not be treated as trusted or private storage.

User-entered post and comment text is rendered as escaped text. Do not add arbitrary HTML, CSS, or JavaScript input. The next milestone introduces a local Django server and SQLite. Before treating it as multi-user or reachable from other machines, implement server-side authentication, authorization, validation, private media delivery, abuse controls, and security tests. A localhost app is not a public service, and local database content is still visible to the device owner.
