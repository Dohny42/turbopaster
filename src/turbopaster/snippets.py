"""Check and merge snippet YAML files into one string-to-string mapping."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from turbopaster.exceptions import (
    ApplicationError,
    ConfigurationError,
    DuplicateSnippetError,
    FileAccessError,
    InvalidExtraPathError,
    InvalidHotkeyError,
    InvalidYamlStructureError,
    InvalidYamlSyntaxError,
    SnippetLoadError,
)

_SUFFIXES = {".yaml", ".yml"}
_MODIFIERS = {"ctrl", "shift", "alt", "meta"}
_KEY_NAMES = {
    "backspace",
    "delete",
    "down",
    "end",
    "enter",
    "escape",
    "home",
    "insert",
    "left",
    "pagedown",
    "pageup",
    "right",
    "space",
    "tab",
    "up",
}


@dataclass(frozen=True)
class _ConfigurationCheck:
    extra_paths: tuple[Path, ...] = ()
    problems: tuple[ApplicationError, ...] = ()


def app_directory() -> Path:
    return Path.home() / "turbopaster"


def load_user_snippets(app_dir: Path | None = None) -> dict[str, str]:
    root = (app_directory() if app_dir is None else app_dir).expanduser()
    snippet_dir = root / "snippets"
    configuration = check_configuration_file(root / "config.yaml")
    if configuration.problems:
        raise ConfigurationError(configuration.problems)

    try:
        snippet_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        reason = exc.strerror or "could not create folder"
        raise FileAccessError(f"{snippet_dir}: {reason}")

    paths = list_snippet_files_in_directory(snippet_dir)
    for extra in configuration.extra_paths:
        if extra.is_dir():
            paths.extend(list_snippet_files_in_directory(extra))
        else:
            paths.append(extra)
    return merge_snippet_files(paths)


def load_directory(directory: Path) -> dict[str, str]:
    paths = list_snippet_files_in_directory(directory)
    return merge_snippet_files(paths)


def list_snippet_files_in_directory(directory: Path) -> list[Path]:
    if not directory.is_dir():
        if directory.exists():
            raise FileAccessError(f"{directory}: not a folder")
        raise FileAccessError(f"{directory}: folder not found")
    try:
        return sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in _SUFFIXES
        )
    except OSError as exc:
        reason = exc.strerror or "could not list folder"
        raise FileAccessError(f"{directory}: {reason}")


def check_configuration_file(path: Path) -> _ConfigurationCheck:
    if not path.exists():
        return _ConfigurationCheck()
    if not path.is_file():
        return _ConfigurationCheck(problems=(FileAccessError(f"{path}: not a file"),))
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _ConfigurationCheck(problems=(FileAccessError(f"{path}: file is not valid UTF-8"),))
    except OSError as exc:
        reason = exc.strerror or "could not read file"
        return _ConfigurationCheck(problems=(FileAccessError(f"{path}: {reason}"),))
    try:
        configuration = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        problem = InvalidYamlSyntaxError(f"{path}: invalid YAML ({_yaml_problem(exc)})")
        return _ConfigurationCheck(problems=(problem,))

    if configuration is None:
        return _ConfigurationCheck()
    if not isinstance(configuration, dict):
        problem = InvalidYamlStructureError(f"{path}: expected a mapping")
        return _ConfigurationCheck(problems=(problem,))

    problems: list[ApplicationError] = []
    for key in configuration:
        if key not in {"extra_paths", "hotkey"}:
            problems.append(InvalidYamlStructureError(f"{path}: unknown setting {key!r}"))

    if "hotkey" in configuration:
        try:
            check_hotkey(configuration["hotkey"])
        except InvalidHotkeyError as exc:
            problems.append(InvalidHotkeyError(f"{path}: {exc}"))

    extra_paths, path_problems = check_extra_paths(
        configuration.get("extra_paths", []),
        path,
    )
    problems.extend(path_problems)
    return _ConfigurationCheck(extra_paths, tuple(problems))


def check_hotkey(hotkey: object) -> None:
    if not isinstance(hotkey, str):
        raise InvalidHotkeyError("hotkey must be a string")

    tokens = [token.strip().casefold() for token in hotkey.split("+")]
    if not hotkey.strip() or any(not token for token in tokens):
        raise InvalidHotkeyError("hotkey must contain non-empty key names separated by '+'")
    if len(tokens) != len(set(tokens)):
        duplicate = next(token for token in tokens if tokens.count(token) > 1)
        raise InvalidHotkeyError(f"hotkey repeats {duplicate!r}")

    if not _MODIFIERS.intersection(tokens):
        raise InvalidHotkeyError("hotkey must include Ctrl, Shift, Alt, or Meta")
    keys = [token for token in tokens if token not in _MODIFIERS]
    if not keys:
        raise InvalidHotkeyError("hotkey must include at least one key")

    for key in keys:
        if key not in _KEY_NAMES and not re.fullmatch(r"[a-z0-9]|f(?:[1-9]|1[0-9]|2[0-4])", key):
            raise InvalidHotkeyError(f"hotkey contains an unsupported key {key!r}")


def check_extra_paths(
    extra_paths: object,
    configuration_path: Path,
) -> tuple[tuple[Path, ...], tuple[ApplicationError, ...]]:
    if extra_paths is None:
        return (), ()
    if not isinstance(extra_paths, list):
        problem = InvalidExtraPathError(
            f"{configuration_path}: extra_paths must be a list of paths"
        )
        return (), (problem,)

    paths: list[Path] = []
    problems: list[ApplicationError] = []
    for index, item in enumerate(extra_paths, start=1):
        if not isinstance(item, str) or not item.strip():
            problems.append(
                InvalidExtraPathError(
                    f"{configuration_path}: extra_paths item {index} must be a path"
                )
            )
            continue

        candidate = Path(item).expanduser()
        if not candidate.is_absolute():
            candidate = configuration_path.parent / candidate
        if candidate.is_dir() or (candidate.is_file() and candidate.suffix.lower() in _SUFFIXES):
            paths.append(candidate)
        elif candidate.is_file():
            problems.append(
                InvalidExtraPathError(
                    f"{configuration_path}: {candidate}: expected a .yaml or .yml file"
                )
            )
        else:
            problems.append(InvalidExtraPathError(f"{configuration_path}: {candidate}: not found"))
    return tuple(paths), tuple(problems)


def check_snippet_files(
    paths: list[Path],
) -> tuple[dict[str, str], tuple[ApplicationError, ...]]:
    merged: dict[str, str] = {}
    defined_at: dict[str, str] = {}
    problems: list[ApplicationError] = []
    for path in paths:
        items, file_problems = parse_snippet_file(path)
        problems.extend(file_problems)
        for key, value, line in items:
            previous = defined_at.get(key)
            if previous is not None:
                problems.append(
                    DuplicateSnippetError(
                        f"duplicate snippet {key!r} in {path}:{line} "
                        f"(already defined in {previous})"
                    )
                )
                continue
            merged[key] = value
            defined_at[key] = f"{path}:{line}"
    return merged, tuple(problems)


def merge_snippet_files(paths: list[Path]) -> dict[str, str]:
    snippets, problems = check_snippet_files(paths)
    if problems:
        raise SnippetLoadError(problems)
    return snippets


def parse_snippet_file(
    path: Path,
) -> tuple[list[tuple[str, str, int]], tuple[ApplicationError, ...]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], (FileAccessError(f"{path}: file not found"),)
    except UnicodeDecodeError:
        return [], (FileAccessError(f"{path}: file is not valid UTF-8"),)
    except OSError as exc:
        reason = exc.strerror or "could not read file"
        return [], (FileAccessError(f"{path}: {reason}"),)

    loader = yaml.SafeLoader(text)
    try:
        try:
            root = loader.get_single_node()
        except yaml.YAMLError as exc:
            return [], (InvalidYamlSyntaxError(f"{path}: invalid YAML ({_yaml_problem(exc)})"),)
        if root is None:
            return [], ()
        if not isinstance(root, yaml.MappingNode):
            try:
                kind = _describe(loader.construct_object(root, deep=True))
            except yaml.YAMLError as exc:
                problem = InvalidYamlSyntaxError(f"{path}: invalid YAML ({_yaml_problem(exc)})")
                return [], (problem,)
            line = root.start_mark.line + 1
            problem = InvalidYamlStructureError(
                f"{path}:{line}: expected a mapping of strings, got {kind}"
            )
            return [], (problem,)

        items: list[tuple[str, str, int]] = []
        problems: list[ApplicationError] = []
        for key_node, value_node in root.value:
            try:
                key_value = loader.construct_object(key_node, deep=True)
                value = loader.construct_object(value_node, deep=True)
            except yaml.YAMLError as exc:
                problems.append(
                    InvalidYamlSyntaxError(f"{path}: invalid YAML ({_yaml_problem(exc)})")
                )
                continue

            line = key_node.start_mark.line + 1
            valid = True
            if not isinstance(key_value, str):
                problems.append(
                    InvalidYamlStructureError(
                        f"{path}:{line}: key must be a string, got {_describe(key_value)}"
                        f"{_string_hint(key_node)}"
                    )
                )
                valid = False
            if not isinstance(value, str):
                label = f"value for {key_value!r}" if isinstance(key_value, str) else "value"
                problems.append(
                    InvalidYamlStructureError(
                        f"{path}:{value_node.start_mark.line + 1}: {label} must be a string, "
                        f"got {_describe(value)}{_string_hint(value_node)}"
                    )
                )
                valid = False
            if valid:
                items.append((key_value, value, line))
        return items, tuple(problems)
    finally:
        loader.dispose()


def _string_hint(node: yaml.Node) -> str:
    if isinstance(node, yaml.ScalarNode):
        return "; quote it so YAML keeps it as text"
    return ""


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
