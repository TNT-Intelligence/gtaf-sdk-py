# GTAF SDK (Python)
Optional integration layer for `gtaf-runtime-py`.

This repository is `gtaf-sdk-py`.

## Purpose
Provide ergonomic helpers and standardized integration patterns on top of the GTAF runtime core.

## Status
This repository is in an early stage and the public API surface is not yet stable.
Current package version: **0.1.0-alpha.1**.

## Scope
This repository currently contains:
- package baseline and versioning surface
- minimal test harness and import validation
- documentation and metadata scaffolding

## Non-Goals
`gtaf-sdk-py` is **not**:
- a replacement for the runtime enforcement core
- a governance interpretation engine
- a policy authoring or evaluation system
- an alternative runtime implementation

## Local Development
Run tests:
```sh
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Repository Structure
- `gtaf_sdk/`: SDK package baseline
- `tests/`: baseline import test

## License
See `LICENSE`.
