# Version policy

Fleet repository versions use Semantic Versioning for the declarative contract:
major for intentionally incompatible inventory/role interfaces, minor for additive
managed capabilities, and patch for compatible fixes or documentation. The fleet
version does not mirror the observer version.

Observer compatibility is expressed only by the exact observer release pin and
`homelab_observer_schema_version`. A fleet release must not broaden a version range
or advance schema support implicitly. Record user-visible changes in `CHANGELOG.md`.
