# Security Policy

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in a public issue. Use
GitHub's private vulnerability reporting feature for this repository. Include
the affected route or component, reproduction steps, impact, and any suggested
mitigation.

## Supported versions

Until the first release, only the current `main` branch receives security fixes.

## Deployment boundary

The reader is designed to be public and read-only. Administration, source
retrieval, refresh, and publishing are private operations and MUST remain
tailnet-only. A deployment MUST pass the public-route boundary tests before
Tailscale Funnel is enabled.
