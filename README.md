# turbopaster

A small, cross-platform text snippet launcher. Search for a name and insert its saved text where you are typing.

Snippets are YAML files that map names to string values. The default location is `$HOME/turbopaster/snippets/`. An empty snippets folder is valid and loads no snippets.
The optional `$HOME/turbopaster/config.yaml` file supports `extra_paths` and `hotkey` settings. Relative extra paths start from the config file's folder. The app checks the config and all snippet files before it uses the snippets. It reports independent problems together.

The `hotkey` setting accepts modifiers (`Ctrl`, `Shift`, `Alt`, or `Meta`) and one or more keys, such as `Ctrl+Shift+Space` or `Ctrl+K+S`. Keys in a multi-key chord are pressed at the same time. Hotkey activation is not implemented yet.

## Run

From the project directory:

```sh
uv run turbopaster
```

`uv run turbopaster` loads configured snippets and prints their names. `uv run turbopaster --search` opens a centered, frameless search palette. Results appear as you type with each snippet's name and a one-line value preview. Multiline values show visible `\n` markers in the preview. The search field is focused on open. Use the arrow keys to move, Enter to select, or Escape to close. Press Ctrl+C in the terminal to exit search mode. Selection prints the snippet's full value. Global hotkey activation and text insertion are not implemented yet.

See [DESIGN.md](DESIGN.md) for the short implementation outline.
