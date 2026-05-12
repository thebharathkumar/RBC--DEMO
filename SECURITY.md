# Security policy

## Reporting a vulnerability

Please email security reports to `bharath.kr702@gmail.com` with subject prefix `[security]`. Include:

- A description of the issue and the impact you expect.
- Steps to reproduce, ideally with a minimal proof of concept.
- The commit hash you tested against.

Do not open public issues for suspected vulnerabilities. You will receive an acknowledgement within seventy two hours and an outline of next steps within five working days.

## Scope

In scope:

- The code in this repository.
- Container images published from this repository.
- Deployments fronted by `rbc-research-platform.onrender.com`.

Out of scope:

- Upstream services (Anthropic, Langfuse, EDGAR, Polygon, Tavily, NewsAPI).
- Denial-of-service findings achievable only with sustained high traffic.
- Findings that require physical access to a developer machine.

## Hardening posture

- Secrets are read only via environment variables. Production deployments fail to boot when required keys are missing (see `apps/api/src/config.py`).
- A prompt injection middleware scans third-party content before it reaches any model context.
- Every external API call is rate-limited and circuit-broken.
- The codebase enforces ruff bandit rules and is scanned by gitleaks on every push.
