# turbopaster

A small, cross-platform text snippet launcher: search for a name and insert its saved text where you are typing.

Snippets are plain YAML files. The planned default location is `$HOME/turbopaster/snippets/`; extra snippet paths and the global hotkey will be configured in `$HOME/turbopaster/config.yaml`.

## Run

From the project directory:

```sh
uv run turbopaster
```

The current prototype loads the example snippets and prints their names. The search window, hotkey, and text insertion are not implemented yet.

See [DESIGN.md](DESIGN.md) for the short implementation outline.
