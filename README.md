# GTAF SDK (Python)
Optional integration layer for `gtaf-runtime-py`.

This repository is `gtaf-sdk-py`.

## Purpose
Provide ergonomic helpers and standardized integration patterns on top of the GTAF runtime core.

## Status
This repository is in an early stage and the public API surface is not yet stable.
Current package version: **0.1.0-alpha.7**.

## Scope
This repository currently contains:
- package baseline and versioning surface
- deterministic runtime input loader API under `gtaf_sdk.artifacts`
- minimal test harness and import validation
- documentation and metadata scaffolding

## Current API Surface
The SDK currently provides a deterministic artifact loader via `load_runtime_inputs` in `gtaf_sdk.artifacts`.

```python
from gtaf_sdk.artifacts import load_runtime_inputs
from gtaf_runtime import enforce

drc, artifacts = load_runtime_inputs(
    drc_path="path/to/drc.json",
    artifacts_dir="path/to/artifacts",
)
result = enforce(drc, context, artifacts)
```

`load_runtime_inputs` resolves artifacts strictly via `drc["refs"]`, with no implicit discovery or heuristics.
It does not modify runtime enforcement semantics and raises explicit SDK exceptions on failure.

The SDK also provides `enforce_from_files` in `gtaf_sdk.enforcement` for direct filesystem-based enforcement wiring.

```python
from gtaf_sdk.enforcement import enforce_from_files

result = enforce_from_files(
    drc_path="path/to/drc.json",
    artifacts_dir="path/to/artifacts",
    context=context,
)
```

`enforce_from_files` delegates to `load_runtime_inputs(...)` and then calls `gtaf_runtime.enforce(...)`.
On loader or I/O failures, it returns an `EnforcementResult` with `outcome="DENY"` and a `reason_code` prefixed with `SDK_`.
Runtime semantics remain unchanged.

For startup checks, the SDK provides structural validation helpers in `gtaf_sdk.validation`.

```python
from gtaf_sdk.validation import warmup_from_files

result = warmup_from_files(
    drc_path="path/to/drc.json",
    artifacts_dir="path/to/artifacts",
)

if not result.ok:
    print(result.errors)
    exit(1)
```

This performs structural startup validation only.
It does not execute enforcement and does not modify runtime semantics.
Its structural DRC validation surface is derived from the runtime contract.

For deterministic action ID shaping, the SDK provides `normalize_action` in `gtaf_sdk.actions`.

```python
from gtaf_sdk.actions import normalize_action

mapping = {"git": "git"}

action_id = normalize_action(
    tool_name="Git",
    arguments={"command": "commit -m 'msg'"},
    mapping=mapping,
)
# -> "git.commit"
```

This performs syntactic normalization only.
It does not perform policy evaluation and does not modify enforcement semantics.

For typed runtime input ergonomics, the SDK provides `ActionId` and `RuntimeContext` in `gtaf_sdk.models`.

```python
from gtaf_sdk.models import ActionId, RuntimeContext

action = ActionId(value="git.commit")
action_id = action.to_str()

context = RuntimeContext(
    scope="ops.prod",
    component="ops.agent",
    interface="ops-api",
    action=action_id,
    extras={"system": "rachel-ai"},
)
payload = context.to_dict()
```

These models are opt-in ergonomics only and do not change enforcement semantics.

For optional telemetry, `enforce_from_files` accepts `TelemetryHooks` from `gtaf_sdk.telemetry`.
Hooks are observational only and do not alter enforcement decisions.
A minimal end-to-end integration example is available at `examples/agent_runtime_integration.py`.

## Quickstart (Minimal Enforcement Wiring)
```python
from gtaf_sdk.actions import normalize_action
from gtaf_sdk.enforcement import enforce_from_files
from gtaf_sdk.models import RuntimeContext

action = normalize_action(tool_name="Git", arguments={"command": "status"}, mapping={"git": "git"})
context = RuntimeContext(
    scope="ops.prod", component="ops.agent", interface="ops-api", action=action
).to_dict()
result = enforce_from_files(
    drc_path="path/to/drc.json", artifacts_dir="path/to/artifacts", context=context
)
if result.outcome == "DENY":
    print(result.reason_code, result.refs)
else:
    print("execute tool here")
```
The SDK does not implement enforcement semantics; it only wires inputs to the deterministic runtime core.

## SDK Compatibility Declaration
### Runtime Compatibility Matrix
The SDK is validated against `gtaf-runtime-py` version line:

- `0.1.x`

Minimum required runtime version: `0.1.0`.

If an incompatible runtime version is detected, SDK validation MUST fail deterministically and MUST NOT introduce fallback allow behavior.

### Semantic Non-Interference Guarantee
The SDK MUST NOT:

- Modify runtime enforcement decisions.
- Remap runtime reason codes.
- Introduce fallback allow behavior.
- Change EXECUTE/DENY semantics.
- Reorder enforcement logic.

The SDK MAY:

- Provide normalization utilities.
- Provide structural validation helpers.
- Provide typed models.
- Provide telemetry hooks.
- Provide convenience wrappers.

Runtime enforcement semantics remain exclusively defined by `gtaf-runtime-py`.

### Breaking Change Definition (SDK Layer)
The following constitute breaking changes at the SDK layer:

- Changes that alter observable enforcement outcomes.
- Changes that alter normalization behavior in a way that breaks existing mappings.
- Removal or semantic change of public SDK APIs.
- Changes that alter expected SDK failure behavior (for example, `SDK_*` error codes).

Breaking changes require a MAJOR version increment.

Minor releases MUST NOT introduce runtime-semantic drift.

### Public SDK Contract Surface
The following are considered stable public SDK APIs:

- `enforce_from_files(...)`
- `warmup_from_files(...)`
- `normalize_action(...)`
- `RuntimeContext`
- `ActionId`
- `TelemetryHooks`

The following are NOT part of the stable contract surface:

- Internal module structure.
- Private helper functions.
- Non-exported utilities.

### Projection Alignment Guarantee
The SDK is projection-aligned, not projection-defining.

Projection semantics are defined exclusively by the runtime contract.

If a Projection MAJOR version changes, the SDK must explicitly declare support before use.

### Versioning Policy
SDK versioning is independent from runtime version numbers.

SDK versions may evolve ergonomics without changing enforcement semantics.

SDK version numbers do not redefine Projection versions.

## Non-Goals
`gtaf-sdk-py` is **not**:
- a replacement for the runtime enforcement core
- a governance interpretation engine
- a policy authoring or evaluation system
- an alternative runtime implementation

## Versioning
This repository follows semantic versioning with pre-releases while the API is still evolving (for example `0.1.0-alpha.N`).

Practical project rules:
- bump the pre-release number for each externally visible SDK API change
- keep version values in sync across `pyproject.toml`, `gtaf_sdk/version.py`, and the README status line
- create stable versions only when the API surface is intentionally declared stable

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
