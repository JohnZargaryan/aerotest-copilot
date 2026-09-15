# Dependency provenance

Resolved on 2026-09-14 from official release repositories, PyPI and npm.
These versions were tested together locally on Windows, not merely guessed.

| Component | Version / source |
| --- | --- |
| Windows portable toolkit | [w64devkit 2.10.0](https://github.com/skeeto/w64devkit/releases/tag/v2.10.0) |
| C++ compiler | GCC 16.2.0, supplied by toolkit |
| CMake / Ninja | 4.4.3 / 1.13.2, supplied by toolkit |
| GoogleTest | [1.18.0](https://github.com/google/googletest/releases/tag/v1.18.0) |
| C++ JSON | [nlohmann/json 3.12.0](https://github.com/nlohmann/json/releases/tag/v3.12.0) |
| Python | 3.12.14 (project requires 3.12.x) |
| FastAPI / Pydantic / Uvicorn | 0.141.1 / 2.13.5 / 0.53.0 |
| pytest / httpx / Ruff | 9.1.1 / 0.28.1 / 0.16.7 |
| Node.js / npm | 25.0.0 / 11.6.2 |
| React / React DOM | 19.3.0 / 19.3.0 |
| TypeScript / Vite / React plugin | 7.0.2 / 8.3.0 / 6.1.1 |

Toolkit published asset SHA256:
`18d0a4c71a166f8401ab6305781bec5882b40b5e06ba9807c61cb5f3b3c6325e`.
Downloaded archive was verified before extraction. CMakeLists.txt pins versions
and computed SHA256 values for C++ library archives fetched from their official
release URLs. Python transitive versions and distribution hashes are in
`requirements.lock`; npm integrity and transitive versions are in `frontend/package-lock.json`.
GitHub Actions are pinned to verified commit SHAs in the workflow.

For a deliberate Python dependency update, use pip-tools 7.6.1, update
requirements.in and matching runtime dependencies in pyproject.toml, then run:

```sh
pip-compile --strip-extras --generate-hashes --output-file requirements.lock requirements.in
```

Reinstall and run all relevant checks. Do not update dependencies silently during
ordinary feature work. Node 25 matches the verified local runtime; consider
a supported LTS baseline before public deployment, with explicit retesting.

Known current warnings: Starlette's TestClient deprecates its httpx integration
and an AnyIO alias. Tests pass and warnings remain visible. Review the testing
client compatibility before future dependency updates. Vite hot reload fails with
`#` in the workspace path; the dev launcher uses a production-build preview there.
Rebuild and refresh after edits, or use a path without `#` for normal hot reload.
