> Publication copy: deployment addresses and domains below are examples; restore private inputs before use.

# Assumptions and unresolved facts

Facts are taken from read-only discovery on 17 July 2026. Items labelled
“assumption” are not represented as verified runtime claims.

- Existing SSH aliases and users remain the operator entry points. BenBeast's
  account could not run passwordless sudo; an encrypted become password may be
  required for its check/apply phases.
- BenNAS responded on port 31722 but rejected the available key. NAS server-side
  state is unverified and remains out of scope; mounted client evidence is used.
- `broker.mqtt` is the reporter's existing configured broker name. BenBeast's
  existing Mosquitto mapping at port 1883 is independently observed. Credentials
  are intentionally unavailable in Git.
- Home Assistant's container is `hass`; its reachable existing HTTPS API route is
  `https://hass.site-2.example.invalid`. The localhost and BenBeast host-IP port 8123
  paths are not published. A Vault/environment token is still required.
- The installed upstream reporter revision is
  `45a20f9760272b88734449b702c289c35058779b` and its script hash matches on all
  three Pis. The upstream code uses a broker-generated client ID; the managed
  role adds one narrow, documented `client_id` configuration patch to satisfy
  stable uniqueness without replacing the reporter.
- Reporter command topics retain their existing upstream shutdown/reboot/service
  command configuration. This repository neither invokes nor exposes those
  commands through MCP.
- The installed Code CLI versions differ (1.98.2 and 1.106.2). Adoption preserves
  existing binaries and each host's authentication directory. A reviewed download
  URL/checksum remains required for a future Pi.
- Restic is not currently installed on the observed hosts. Backup execution is
  therefore ready in code but unverified until approved deployment and NAS auth.
- Fresh MQTT publications, HA registry devices/entities, and fresh HA state have
  not been claimed until `scripts/verify-telemetry` runs with credentials.
- BenBeast CPU package temperature is a host-local MQTT publisher
  (`/home/ben/benbeast-cpu-temp`, client `homelab-benbeast-cpu`, user
  `mqtt-benbeast`), not part of `homelab-observer` or the Pi reporter role.
  Home Assistant discovery entity is `sensor.benbeast_cpu_temperature`.
- Idempotence is not claimed until two approved applies have been observed with
  the second producing zero changes. Local static/idempotence-oriented tests alone
  do not prove production idempotence.
