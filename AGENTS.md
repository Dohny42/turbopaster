# Project Guidelines

## Base
- Prioritize user experience first, developer experience second, and performance third. Keep the first release small and cross-platform.
- Develop incrementally. Before implementing a feature or feature batch, discuss its scope and proposed steps, get the user's approval, then implement only the approved slice. Interrupt to clarify consequential ambiguities rather than guessing.
- Keep error handling correct and actionable, but do not add defensive checks for speculative failure modes. Use project-specific exception types from `src/turbopaster/exceptions.py`; add or move an exception there when touching the relevant behavior rather than introducing unrelated changes.
- Ask for explicit permission before installing or adding any dependency. Explain what it does and why it is needed first. Use `uv` for Python package and environment management.
- Routine navigation and non-destructive commands may proceed without approval. Ask before creating or removing folders, deleting or overwriting user data, or running any potentially dangerous command.
- Keep `README.md` current with user-facing setup, commands, and implemented behavior. Keep `DESIGN.md` current with implementation decisions, constraints, and unresolved questions. Update both when a change affects both audiences; do not copy implementation detail into the README.

## Python
- The supported floor is Python 3.14 (`requires-python` in `pyproject.toml`). Use modern Python type syntax and built-in generic types, while remaining compatible with that declared floor. Add useful annotations to new or changed code.
- Use `uv` for dependency changes and Python project commands; keep `uv.lock` consistent when dependencies change. Never install a new dependency without the user's prior approval.
- Keep custom exception classes in `src/turbopaster/exceptions.py`. Prefer the existing project structure and public APIs; avoid unrelated refactors.

## Product Design
- This is a local text-snippet launcher targeting Windows, macOS, and Linux: a global hotkey opens a polished search UI, the user searches snippet names, and confirming inserts the selected text at the current cursor.
- Snippets are YAML files containing only string-to-string mappings; multiline string values are supported. Default snippets are in `$HOME/turbopaster/snippets/`. `$HOME/turbopaster/config.yaml` supports top-level `extra_paths` and `hotkey` settings. Duplicate names and invalid YAML or schema must produce actionable errors, never silently override data.
- The interaction design requires Escape to cancel, hiding the search window before insertion, and restoring the user's clipboard afterward. Keep unspecified hotkey syntax, platform behavior, and implementation choices open for discussion until agreed.
- Do not add deferred features such as snippet groups, clipboard history, or additional snippet formats without approval. Keep the GUI consistent with the approved Qt Quick/QML command palette direction; discuss and get approval before changing the UI framework or interaction design.
- The preferred initial hotkey is Ctrl+Shift+Space on all target platforms, subject to checking OS and application conflicts. Before implementation, propose the config value syntax and conflict behavior and get agreement. Detailed visual and insertion choices remain open for discussion.

## Tests and Verification
- Before suggesting any tests, present a concise proposal with a stable ID for each test, its test name, purpose, and level (`unit`, `integration`, or `end-to-end`). The user can approve or discuss tests by ID. Do not add or run tests until the user approves the relevant IDs.
- For complex tests, document the purpose in a `GIVEN -> WHEN -> THEN` format for human readability. GIVEN conditions may chain with `AND` or `OR`.
- Aim for a stable test pyramid: focused unit tests for logic, integration tests for important component boundaries, and a small number of end-to-end tests for critical user workflows. Choose the mix based on the feature and avoid brittle OS-, timing-, or display-dependent tests where a reliable seam is available.
- Do not run the application or tests before approval. Once the user approves test IDs, the agent may execute those approved tests; report commands and results clearly.
- After implementation, identify what was verified and what remains for the user to run. Do not install test tooling or other dependencies without permission.

## Project Documentation
- Write English prose with at least 80% compliance with ASD-STE100. Prefer short, direct sentences and simple grammar. Apply this to documentation, user-facing messages, comments, and test descriptions. Do not change code identifiers or established technical terms only to meet this rule.
- `README.md` is the source for users: describe only behavior that is implemented, plus accurate setup and run instructions.
- `DESIGN.md` is the source for implementation details: record the agreed architecture, behavior, constraints, decisions, and next milestone. Keep pending decisions explicit; do not present proposals as settled requirements.
