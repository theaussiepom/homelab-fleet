# Releasing homelab-fleet

Fleet releases are private Git tags; they do not publish Python artifacts. From a
clean reviewed commit, update the project version and `CHANGELOG.md`, run
`make test`, preserve relevant check-mode evidence, then create an annotated tag:

```sh
git status --short
make test
git tag -a vX.Y.Z -m "homelab-fleet X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Pushing and any production apply require separate approval. Never retag an
existing release or force-push. Observer wheel publication is documented in the
observer repository; fleet records only the reviewed immutable consumer pin.
