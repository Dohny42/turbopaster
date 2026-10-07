# turbopaster

A small, cross-platform text snippet launcher. Search for a name and insert its saved text where you are typing.

Snippets are YAML files that map names to string values. The default location is `$HOME/turbopaster/snippets/`. An empty snippets folder is valid and loads no snippets.
The optional `$HOME/turbopaster/config.yaml` file supports `extra_paths` and `hotkey` settings. Relative extra paths start from the config file's folder. The app checks the config and all snippet files before it uses the snippets. It reports independent problems together.

The `hotkey` setting accepts modifiers (`Ctrl`, `Shift`, `Alt`, or `Meta`) and one or more keys, such as `Ctrl+Shift+Space` or `Ctrl+K+S`. Keys in a multi-key chord are pressed at the same time. The default hotkey is `Ctrl+Shift+Space`.

## Run

From the project directory:

```sh
uv run turbopaster
```

`uv run turbopaster` starts a resident launcher. Press the configured hotkey to open the centered, frameless search palette. Results appear as you type with each snippet's name and a one-line value preview. Multiline values show visible `\n` markers in the preview. The search field is focused on open. Use the arrow keys to move, Enter to select, or Escape to hide the palette. Selection also hides the palette. Press Ctrl+C in the terminal to exit.

`uv run turbopaster --search` opens the palette without a global hotkey and exits when the palette closes. `uv run turbopaster --list` loads snippets and prints their names. Text insertion at the cursor is not implemented yet. The selected value is printed when the process exits.

See [DESIGN.md](DESIGN.md) for the short implementation outline.
