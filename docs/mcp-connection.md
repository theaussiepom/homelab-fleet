# Private MCP connection

The gateway is a local-disk systemd service on BenBeast and listens only at
`127.0.0.1:8765`. It uses Streamable HTTP at `/mcp`. No public listener, reverse
proxy, Cloudflare, or Authentik change is included.

Create a private SSH tunnel from an authorised workstation:

```sh
ssh -N -L 8765:127.0.0.1:8765 BenBeast
```

Export the Vault-provisioned local test bearer token without writing it to shell
history, copy `.codex/config.toml.example` to `.codex/config.toml`, and connect to
`http://127.0.0.1:8765/mcp`. The example reads the bearer token from
`HOMELAB_MCP_BEARER_TOKEN`.

The gateway refuses client-supplied IPs, uses inventory-selected addresses,
BatchMode, strict known hosts, no forwarding, a dedicated key, concurrency/time/
output caps, response redaction, and per-tool audit. All fixed tools are annotated
read-only/non-destructive/open-world. `run_non_sudo` is deliberately annotated
non-read-only and non-idempotent so clients request approval.
