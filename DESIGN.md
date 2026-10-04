# turbopaster

Hotkey search for inserting named text at the cursor. Keep the first version small and cross-platform, with a centered, frameless Qt Quick/QML command palette.

## Data and configuration

- Snippets are YAML files containing only `dict[str, str]`; multiline values are supported.
- Default snippets live in `$HOME/turbopaster/snippets/`.
- Global settings live in `$HOME/turbopaster/config.yaml`.
- The config uses top-level `extra_paths` and `hotkey` keys. Future settings can be added as separate keys.
- Duplicate names and invalid YAML/schema are actionable errors; never silently override a snippet.

Ctrl+Shift+Space is the preferred initial hotkey on Windows, macOS, and Linux. The config value syntax and conflict behavior must be agreed before implementation.

## Interaction

Open the search palette with a global hotkey, filter by snippet name, and confirm to insert. Initially show only the search field; reveal matching results beneath it as the user types and animate the palette height. Arrow keys move the selection, Enter confirms, and Escape closes without selecting. Hide the window before pasting. Preserve the user's clipboard after insertion.

## Development

- Complete: snippet loading and validation.
- Complete: interactive Qt Quick/QML search palette, available with `--search`; it focuses the search field on open, shows a one-line value preview under each matching name, and returns/prints the selected snippet's full value. Insertion at the cursor is not implemented yet.
- Next: agree on hotkey config syntax and conflict behavior, then add the global hotkey and connect it to the search window.
- After that: hide the window, insert the selected text at the cursor, and restore the user's clipboard.

Agree on each feature step before proceeding. Before suggesting tests, provide test IDs and names for approval. Approved tests may be run by the agent.

Clipboard history, groups, additional formats, and other settings are future work.
