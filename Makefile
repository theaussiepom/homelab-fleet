.PHONY: test unit lint syntax shellcheck inventory-check secret-scan

test: unit lint syntax shellcheck inventory-check secret-scan

unit:
	uv run pytest -q

lint:
	uv run ruff check tests scripts/check-inventory
	uv run ruff format --check tests scripts/check-inventory
	uv run mypy tests
	uv run yamllint .
	uv run ansible-lint playbooks roles

syntax:
	@set -eu; for playbook in playbooks/*.yml; do \
		uv run ansible-playbook -i localhost, --syntax-check "$$playbook"; \
	done

shellcheck:
	@for file in scripts/* roles/*/files/*; do \
		if [ -f "$$file" ] && head -1 "$$file" | grep -q 'bash'; then uv run shellcheck "$$file"; fi; \
	done

inventory-check:
	@tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	uv run python scripts/fleet_catalog.py --catalog examples/fleet-catalog.json --out "$$tmp/inventory" && \
	uv run python scripts/check-inventory --skip-secrets --catalog examples/fleet-catalog.json --inventory "$$tmp/inventory"

secret-scan:
	uv run python scripts/check-inventory --secrets-only
