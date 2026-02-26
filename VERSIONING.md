# SDK Versioning Policy

## Scope

This policy applies to `gtaf-sdk` package versioning and compatibility guarantees.

## Contract Surface

The stable public SDK surface is documented in `README.md` under "Public SDK Contract Surface".
Runtime enforcement semantics remain defined by `gtaf-runtime`.

## Semantic Versioning Rules

- Patch (`x.y.Z`): non-breaking fixes and release hygiene updates.
- Minor (`x.Y.z`): additive, backward-compatible SDK functionality.
- Major (`X.y.z`): any breaking SDK API or behavior change.

## Breaking Change Classification

The following require a MAJOR version increment:

- removal or semantic change of public SDK APIs,
- changes that alter observable enforcement outcomes,
- changes that alter normalization contract behavior,
- changes that alter expected SDK failure behavior (`SDK_*` codes).

## Runtime Compatibility Rule

- SDK dependency constraint is `gtaf-runtime>=0.1.0,<0.2.0`.
- SDK must consume only documented runtime public API symbols.
- Runtime-semantic drift is not permitted in patch or minor releases.

## Tagging Rule

Release tags must follow `vX.Y.Z` and match package metadata exactly.

## Documentation Alignment Rule

Before release, ensure consistency across:
- `pyproject.toml`
- `gtaf_sdk/version.py`
- `README.md`
