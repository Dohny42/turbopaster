"""Load snippet YAML files into one string-to-string mapping."""

import os
import sys
from pathlib import Path

import yaml

_SUFFIXES = {".yaml", ".yml"}


class SnippetError(Exception):
    """A snippet file the user can fix."""


def app_directory() -> Path:
    if sys.platform == "win32":
        root = os.environ.get("APPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        root = os.environ.get("XDG_CONFIG_HOME")
        base = Path(root) if root else Path.home() / ".config"
    return base / "turbopaster"


def load_user_snippets(app_dir: Path | None = None) -> dict[str, str]:
    root = app_directory() if app_dir is None else app_dir
    snippet_dir = root / "snippets"
    config = root / "config.yaml"
    try:
        snippet_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        reason = exc.strerror or "could not create folder"
        raise SnippetError(f"{snippet_dir}: {reason}") from None

    paths = _snippet_files(snippet_dir)
    for extra in _extra_paths(config):
        if extra.is_dir():
            paths.extend(_snippet_files(extra))
        elif extra.is_file():
            if extra.suffix.lower() not in _SUFFIXES:
                raise SnippetError(f"{extra}: expected a .yaml or .yml file")
            paths.append(extra)
        else:
            raise SnippetError(f"{extra}: not found")
    if not paths:
        raise SnippetError(
            f"no snippet files in {snippet_dir}; add yaml files there, "
            f"or list more paths under extra in {config}"
        )
    return load_files(paths)


def load_directory(directory: Path) -> dict[str, str]:
    paths = _snippet_files(directory)
    if not paths:
        raise SnippetError(f"{directory}: no .yaml or .yml files")
    return load_files(paths)


def _snippet_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        if directory.exists():
            raise SnippetError(f"{directory}: not a folder")
        raise SnippetError(f"{directory}: folder not found")
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in _SUFFIXES
    )


def _extra_paths(path: Path) -> list[Path]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise SnippetError(f"{path}: file is not valid UTF-8") from None
    except OSError as exc:
        reason = exc.strerror or "could not read file"
        raise SnippetError(f"{path}: {reason}") from None
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SnippetError(f"{path}: invalid YAML ({_yaml_problem(exc)})") from None
    if loaded is None:
        return []
    if not isinstance(loaded, dict):
        raise SnippetError(f"{path}: expected a mapping")
    unknown = [key for key in loaded if key != "extra"]
    if unknown:
        raise SnippetError(f"{path}: unknown setting {unknown[0]!r}")
    extra = loaded.get("extra", [])
    if extra is None:
        return []
    if not isinstance(extra, list):
        raise SnippetError(f"{path}: extra must be a list of paths")

    paths: list[Path] = []
    for index, item in enumerate(extra, start=1):
        if not isinstance(item, str) or not item.strip():
            raise SnippetError(f"{path}: extra item {index} must be a path")
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        paths.append(candidate)
    return paths


def load_files(paths: list[Path]) -> dict[str, str]:
    merged: dict[str, str] = {}
    defined_at: dict[str, str] = {}
    for path in paths:
        for key, value, line in _load_file(path):
            previous = defined_at.get(key)
            if previous is not None:
                raise SnippetError(
                    f"duplicate snippet {key!r} in {path}:{line} "
                    f"(already defined in {previous})"
                )
            merged[key] = value
            defined_at[key] = f"{path}:{line}"
    return merged


def _load_file(path: Path) -> list[tuple[str, str, int]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SnippetError(f"{path}: file not found") from None
    except UnicodeDecodeError:
        raise SnippetError(f"{path}: file is not valid UTF-8") from None
    except OSError as exc:
        reason = exc.strerror or "could not read file"
        raise SnippetError(f"{path}: {reason}") from None

    loader = yaml.SafeLoader(text)
    try:
        try:
            root = loader.get_single_node()
        except yaml.YAMLError as exc:
            raise SnippetError(f"{path}: invalid YAML ({_yaml_problem(exc)})") from None
        if root is None:
            return []
        if not isinstance(root, yaml.MappingNode):
            line = root.start_mark.line + 1
            kind = _describe(_construct(path, loader, root))
            raise SnippetError(
                f"{path}:{line}: expected a mapping of strings, got {kind}"
            )
        items: list[tuple[str, str, int]] = []
        for key_node, value_node in root.value:
            key = _as_string(
                path,
                key_node,
                _construct(path, loader, key_node),
                what="key",
            )
            value = _as_string(
                path,
                value_node,
                _construct(path, loader, value_node),
                what=f"value for {key!r}",
            )
            items.append((key, value, key_node.start_mark.line + 1))
        return items
    finally:
        loader.dispose()


def _construct(path: Path, loader: yaml.SafeLoader, node: yaml.Node) -> object:
    try:
        return loader.construct_object(node, deep=True)
    except yaml.YAMLError as exc:
        raise SnippetError(f"{path}: invalid YAML ({_yaml_problem(exc)})") from None


def _as_string(path: Path, node: yaml.Node, value: object, *, what: str) -> str:
    if isinstance(value, str):
        return value
    line = node.start_mark.line + 1
    hint = ""
    if isinstance(node, yaml.ScalarNode):
        hint = "; quote it so YAML keeps it as text"
    raise SnippetError(
        f"{path}:{line}: {what} must be a string, got {_describe(value)}{hint}"
    )


def _describe(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"bool ({str(value).lower()})"
    if isinstance(value, int | float):
        return f"{type(value).__name__} ({value})"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "a list"
    if isinstance(value, dict):
        return "a mapping"
    return type(value).__name__


def _yaml_problem(exc: yaml.YAMLError) -> str:
    problem = getattr(exc, "problem", None)
    mark = getattr(exc, "problem_mark", None)
    if isinstance(problem, str) and mark is not None:
        return f"line {mark.line + 1}: {problem}"
    text = str(exc).strip()
    return text or "could not parse file"
