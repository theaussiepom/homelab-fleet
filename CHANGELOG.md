# Changelog

All notable changes to homelab-fleet are recorded here. This project follows
Semantic Versioning; dates use ISO 8601.

## [0.1.0] - 2026-07-17

- Preserved the combined implementation at annotated tag `monorepo-split-base`.
- Removed observer application source after extracting its useful history into an
  independent repository.
- Added immutable observer version, release URL, SHA-256, and schema pins.
- Converted observer roles to install a released wheel and render runtime policy
  from inventory without repository coupling.
- Added repository-boundary, pin, inheritance, secret, lint, and syntax gates.
