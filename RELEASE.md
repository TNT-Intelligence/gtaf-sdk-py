# Release Process (`gtaf-sdk`)

This document defines the minimal release procedure for `gtaf-sdk`.

## 1. Version Bump Policy

Use semantic versioning (`MAJOR.MINOR.PATCH`) for package releases.

- Patch (`x.y.Z`): packaging/docs/CI updates and bug fixes without SDK contract changes.
- Minor (`x.Y.z`): additive, backward-compatible SDK capabilities.
- Major (`X.y.z`): breaking SDK contract changes (API removals or semantic behavior changes).

Before release:
- Update version in `pyproject.toml` and `gtaf_sdk/version.py`.
- Ensure README status/version references remain aligned.
- Ensure compatibility declaration remains aligned with `gtaf-runtime`.

## 2. Tag Creation Policy

Release tags must follow `vX.Y.Z` and match `pyproject.toml` exactly.

Example:

```sh
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
```

Notes:
- Create tags only from reviewed commits on `main`.
- Do not retag an existing released version.

## 3. Pre-Release Validation

Run the same checks enforced by CI:

```sh
python -m unittest discover -s tests -p "test_*.py" -v
python -m build
python -m twine check dist/*
```

Packaging smoke test in a clean virtual environment:

```sh
python -m venv venv_test
source venv_test/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python -c "import gtaf_sdk"
python -c "from gtaf_sdk.enforcement import enforce_from_files"
deactivate
```

## 4. Build and Publish (PyPI)

Build artifacts:

```sh
python -m pip install --upgrade pip build twine
python -m build
```

Validate distribution metadata:

```sh
python -m twine check dist/*
```

Upload artifacts:

```sh
python -m twine upload dist/*
```

## 5. Changelog Expectation

Each release should include release notes covering:
- version number and date,
- user-visible changes,
- compatibility impact (if any),
- migration notes for breaking releases.

If no dedicated `CHANGELOG.md` exists, include release notes in the release PR and/or GitHub release notes.

## 6. Artifact Content Notes

- Wheel artifacts must not include `tests/`.
- Source distributions may include `tests/` intentionally for source-level verification.
