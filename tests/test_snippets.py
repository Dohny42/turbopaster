from pathlib import Path

import pytest

from turbopaster.main import main
from turbopaster.snippets import (
    SnippetError,
    app_directory,
    load_directory,
    load_files,
    load_user_snippets,
)


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_multiline_strings(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "shared.yaml",
        "email: user@example.com\nsig: |-\n  Best regards,\n  Name\n",
    )

    assert load_files([path]) == {
        "email": "user@example.com",
        "sig": "Best regards,\nName",
    }


def test_empty_file_is_an_empty_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "empty.yaml", "")

    assert load_files([path]) == {}


def test_comments_only_file_is_an_empty_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "notes.yaml", "# nothing yet\n")

    assert load_files([path]) == {}


def test_rejects_non_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "- just\n- a\n- list\n")

    with pytest.raises(SnippetError, match="expected a mapping of strings, got a list"):
        load_files([path])


def test_rejects_non_string_value_and_names_the_key(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "pin: 123\n")

    with pytest.raises(
        SnippetError,
        match=r"value for 'pin' must be a string, got int \(123\); quote it",
    ):
        load_files([path])


def test_rejects_bool_key(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "yes: hello\n")

    with pytest.raises(SnippetError, match="key must be a string, got bool"):
        load_files([path])


def test_rejects_null_value(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "note:\n")

    with pytest.raises(SnippetError, match="value for 'note' must be a string, got null"):
        load_files([path])


def test_rejects_duplicate_key_in_one_file(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "email: a@b.c\nemail: c@d.e\n")

    with pytest.raises(
        SnippetError,
        match=r"duplicate snippet 'email' in .*bad\.yaml:2 \(already defined in .*bad\.yaml:1\)",
    ):
        load_files([path])


def test_rejects_duplicate_key_across_files(tmp_path: Path) -> None:
    first = _write(tmp_path / "a.yaml", "email: a@b.c\n")
    second = _write(tmp_path / "b.yaml", "email: c@d.e\n")

    with pytest.raises(
        SnippetError,
        match=r"duplicate snippet 'email' in .*b\.yaml:1 \(already defined in .*a\.yaml:1\)",
    ):
        load_files([first, second])


def test_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "email: [\n")

    with pytest.raises(SnippetError, match="invalid YAML"):
        load_files([path])


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SnippetError, match="file not found"):
        load_files([tmp_path / "missing.yaml"])


def test_rejects_non_utf8(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(SnippetError, match="not valid UTF-8"):
        load_files([path])


def test_merges_directory_in_name_order(tmp_path: Path) -> None:
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    _write(snippets / "b.yaml", "beta: two\n")
    _write(snippets / "a.yaml", "alpha: one\n")

    assert list(load_directory(snippets)) == ["alpha", "beta"]


def test_directory_errors(tmp_path: Path) -> None:
    missing = tmp_path / "snippets"
    with pytest.raises(SnippetError, match="folder not found"):
        load_directory(missing)

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SnippetError, match="no .yaml or .yml files"):
        load_directory(empty)


def test_load_user_snippets_uses_explicit_app_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "example.yaml", "email: user@example.com\n")

    assert load_user_snippets(app_dir) == {"email": "user@example.com"}


def test_load_user_snippets_creates_snippets_dir_and_returns_empty_mapping(
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"

    assert load_user_snippets(app_dir) == {}
    assert (app_dir / "snippets").is_dir()


def test_load_user_snippets_merges_extra_file_and_directory(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "base.yaml", "base: one\n")
    extra_dir = app_dir / "shared"
    extra_dir.mkdir()
    _write(extra_dir / "shared.yaml", "shared: two\n")
    _write(app_dir / "more.yaml", "more: three\n")
    _write(
        app_dir / "config.yaml",
        "extra_paths:\n  - shared\n  - more.yaml\n",
    )

    assert load_user_snippets(app_dir) == {
        "base": "one",
        "shared": "two",
        "more": "three",
    }


def test_load_user_snippets_resolves_relative_extra_paths(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    extra_dir = tmp_path / "outside" / "snippets"
    extra_dir.mkdir(parents=True)
    _write(extra_dir / "extra.yaml", "extra: loaded\n")
    _write(
        app_dir / "config.yaml",
        "extra_paths:\n  - ../outside/snippets\n",
    )

    assert load_user_snippets(app_dir) == {"extra": "loaded"}


def test_load_user_snippets_expands_user_in_app_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    app_dir = home / "custom-app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "example.yaml", "email: user@example.com\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    assert load_user_snippets(Path("~/custom-app")) == {
        "email": "user@example.com"
    }


def test_load_user_snippets_reports_missing_extra_path(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "extra_paths:\n  - missing.yaml\n")

    with pytest.raises(SnippetError, match="missing.yaml: not found"):
        load_user_snippets(app_dir)


def test_app_directory_defaults_to_home_turbopaster(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert app_directory() == tmp_path / "turbopaster"


def test_config_rejects_non_list_extra_paths(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "extra_paths: shared\n")

    with pytest.raises(SnippetError, match="extra_paths must be a list of paths"):
        load_user_snippets(app_dir)


def test_config_rejects_non_string_extra_path(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "extra_paths:\n  - true\n")

    with pytest.raises(SnippetError, match="extra_paths item 1 must be a path"):
        load_user_snippets(app_dir)


def test_config_rejects_non_string_hotkey(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "hotkey: 123\n")

    with pytest.raises(SnippetError, match="hotkey must be a string"):
        load_user_snippets(app_dir)


def test_config_rejects_unknown_setting(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "unexpected: value\n")

    with pytest.raises(SnippetError, match="unknown setting 'unexpected'"):
        load_user_snippets(app_dir)


def test_main_prints_names_from_explicit_app_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    app_dir = tmp_path / "app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "example.yaml", "email: user@example.com\n")

    main(["--app-dir", str(app_dir)])

    assert capsys.readouterr().out.splitlines() == [
        "loaded 1 snippets",
        "  email",
    ]


def test_main_reports_schema_error_from_explicit_app_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    app_dir = tmp_path / "app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "bad.yaml", "pin: 1\n")

    with pytest.raises(SystemExit) as exc:
        main(["--app-dir", str(app_dir)])

    assert exc.value.code == 1
    error = capsys.readouterr().err
    assert error.startswith("turbopaster:")
    assert "pin" in error
