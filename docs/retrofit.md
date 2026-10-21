# Safe retrofit and rollout

Every phase starts with local tests and a host-limited `--check --diff`. Save the
diff, state the exact affected paths, and obtain explicit approval before apply.
Keep all safety variables false unless a reviewed phase explicitly needs one.

1. Discovery only: `playbooks/discover.yml`.
2. Local repository tests: `make test`.
3. Full check: `ansible-playbook playbooks/adopt.yml --check --diff`.
4. ZigbeePi observer roles only. Verify `zigbee2` and `zwave-js-ui` status/logs.
5. ZigbeePi reporter/Code Tunnel. Run full MQTT/HA telemetry verification.
6. LoungeOTBR reporter/observer. Verify OTBR REST, role, USB, watchdog, and that
   spare BLE-only Matter remains stopped with restart `no`.
7. Pironman adoption. Verify OTBR, primary Matter, Pi-hole2, Unbound2, ThreadLens,
   Pironman, and ser2net.
8. BenBeast probe/gateway. Verify `hass` and the existing MQTT broker first.
9. Install NFS/systemd files host by host without starting NFS or restarting Docker.
10. In a later separately approved window, reboot one host at a time and prove
    NFS-before-Docker behaviour before proceeding.

Study Matter remains primary. Lounge Matter remains BLE-only, `restart: no`, and
normally stopped. OTBR router/leader plus REST health does not imply sleepy Thread
end devices are immediately available; after a long outage allow 10–20+ minutes
for them to reattach.

Exact per-phase rollback is in [rollback.md](rollback.md).
