# Security notes

This release is a local, single-browser showcase with fictional sample data. It has no accounts, server endpoints, secrets, uploads, or payment processing. Browser storage is editable by the browser owner and must not be treated as trusted or private storage.

User-entered post and comment text is rendered as escaped text. Do not add arbitrary HTML, CSS, or JavaScript input. Before any networked or multi-user release, implement server-side authentication, authorization, validation, private media delivery, abuse controls, and security tests; the present prototype does not provide those protections.
