# turbopaster

Hotkey search for inserting named text at the cursor. Keep the first version small and cross-platform, with a centered, frameless Qt Quick/QML command palette.

## Data and configuration

- Snippets are YAML files containing only `dict[str, str]`; multiline values are supported.
- Default snippets live in `$HOME/turbopaster/snippets/`.
- An existing empty snippets folder is valid and loads an empty mapping.
- Global settings live in `$HOME/turbopaster/config.yaml`.
- The config supports top-level `extra_paths` and `hotkey` keys. Relative extra paths start from the config file's folder.
- Validate configuration before scanning or loading snippets. Collect independent configuration and snippet problems and report them together.
- Duplicate names and invalid YAML/schema are actionable errors. Never silently override a snippet.
- Custom application errors live in `exceptions.py`. The CLI catches `ApplicationError` and reports the stored problems.

The hotkey format uses `+` between tokens. It requires at least one modifier (`Ctrl`, `Shift`, `Alt`, or `Meta`) and one or more keys. Multiple keys form a simultaneous chord, such as `Ctrl+K+S`. The default is `Ctrl+Shift+Space`. The app converts this format to the syntax used by `pynput`.

Do not scan other applications for hotkey conflicts. The user is responsible for selecting an available chord. If a platform registration API reports a conflict when activation is implemented, report that failure.

## Interaction

Open the search palette with a global hotkey, filter by snippet name, and confirm to insert. Initially show only the search field; reveal matching results beneath it as the user types and animate the palette height. Arrow keys move the selection, Enter confirms, and Escape hides the resident palette without selecting. Queue hotkey callbacks onto the Qt thread before changing window state. Hide the window before pasting. Preserve the user's clipboard after insertion.

## Development

- Complete: configuration and snippet validation. Report independent problems together before returning any snippets.
- Complete: interactive Qt Quick/QML search palette. The default command runs in resident mode with a global hotkey. The `--search` option opens the palette without a listener, and `--list` prints snippet names. The palette focuses the search field on open, shows a one-line value preview under each matching name, hides after selection or Escape in resident mode, and exits on Ctrl+C. The selected value is printed when the process exits.
- Complete: global hotkey activation with `Ctrl+Shift+Space` as the default and simultaneous multi-key chords supported. Do not add cross-application conflict scanning. Listener startup failures are reported.
- Next: insert the selected text at the cursor and restore the user's clipboard.

Agree on each feature step before proceeding. Before suggesting tests, provide test IDs and names for approval. Approved tests may be run by the agent.

Clipboard history, groups, additional formats, and other settings are future work.
