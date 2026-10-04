# turbopaster

A small, cross-platform text snippet launcher: search for a name and insert its saved text where you are typing.

Snippets are plain YAML files. The planned default location is `$HOME/turbopaster/snippets/`; extra snippet paths and the global hotkey will be configured in `$HOME/turbopaster/config.yaml`.

## Run

From the project directory:

```sh
uv run turbopaster
```

`uv run turbopaster` loads configured snippets and prints their names. `uv run turbopaster --search` opens a centered, frameless search palette. Results appear as you type with each snippet's name and a one-line value preview; multiline values show visible `\n` markers in the preview. The search field is focused on open. Use the arrow keys to move, Enter to select, or Escape to close. Selection prints the snippet's full value; global hotkey activation and text insertion are not implemented yet.

See [DESIGN.md](DESIGN.md) for the short implementation outline.
