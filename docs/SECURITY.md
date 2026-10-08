# Security Review

## Strengths
* Strict RBAC is enforced on routes.
* Passwords hashed via `pwdlib` with anti-timing-attack dummy verification.
* Valid JWT required for all domain endpoints.
* ORM prevents SQL injection.

## Weaknesses (Action Required)
* **CRITICAL:** Secrets (`SECRET_KEY`, DB creds) are stored in an uncommitted `.env` file, but there is no `.env.example`.
* **MEDIUM:** Missing rate-limiting on login endpoints.
