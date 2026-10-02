# turbopaster

Hotkey search for inserting named text at the cursor. Keep the first version small and cross-platform, with a simple Tkinter window.

## Data and configuration

- Snippets are YAML files containing only `dict[str, str]`; multiline values are supported.
- Default snippets live in `$HOME/turbopaster/snippets/`.
- Global settings live in `$HOME/turbopaster/config.yaml`.
- The config uses top-level `extra_paths` and `hotkey` keys. Future settings can be added as separate keys.
- Duplicate names and invalid YAML/schema are actionable errors; never silently override a snippet.

The hotkey value syntax is still to be agreed before implementation.

## Interaction

Open the search window with a global hotkey, filter by snippet name, and confirm to insert. Escape closes without inserting. Hide the window before pasting. Preserve the user's clipboard after insertion.

## Development

Build incrementally: validate snippet loading, then the search window, then the global hotkey, then insertion. Agree on each step before proceeding. Propose tests for approval before adding or running them; the user will run the program and approved tests.

Clipboard history, groups, additional formats, and other settings are future work.
