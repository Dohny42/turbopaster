from pathlib import Path

import pytest

from turbopaster.exceptions import (
    ConfigurationError,
    DuplicateSnippetError,
    FileAccessError,
    InvalidExtraPathError,
    InvalidHotkeyError,
    InvalidYamlSyntaxError,
    SnippetLoadError,
)
from turbopaster.main import main
from turbopaster.snippets import (
    app_directory,
    check_configuration_file,
    check_hotkey,
    check_snippet_files,
    load_directory,
    load_user_snippets,
    merge_snippet_files,
)


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_multiline_strings(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "shared.yaml",
        "email: user@example.com\nsig: |-\n  Best regards,\n  Name\n",
    )

    assert merge_snippet_files([path]) == {
        "email": "user@example.com",
        "sig": "Best regards,\nName",
    }


def test_empty_file_is_an_empty_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "empty.yaml", "")

    assert merge_snippet_files([path]) == {}


def test_comments_only_file_is_an_empty_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "notes.yaml", "# nothing yet\n")

    assert merge_snippet_files([path]) == {}


def test_rejects_non_mapping(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "- just\n- a\n- list\n")

    with pytest.raises(SnippetLoadError, match="expected a mapping of strings, got a list"):
        merge_snippet_files([path])


def test_rejects_non_string_value_and_names_the_key(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "pin: 123\n")

    with pytest.raises(
        SnippetLoadError,
        match=r"value for 'pin' must be a string, got int \(123\); quote it",
    ):
        merge_snippet_files([path])


def test_rejects_bool_key(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "yes: hello\n")

    with pytest.raises(SnippetLoadError, match="key must be a string, got bool"):
        merge_snippet_files([path])


def test_rejects_null_value(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "note:\n")

    with pytest.raises(SnippetLoadError, match="value for 'note' must be a string, got null"):
        merge_snippet_files([path])


def test_rejects_duplicate_key_in_one_file(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "email: a@b.c\nemail: c@d.e\n")

    with pytest.raises(
        SnippetLoadError,
        match=r"duplicate snippet 'email' in .*bad\.yaml:2 \(already defined in .*bad\.yaml:1\)",
    ):
        merge_snippet_files([path])


def test_rejects_duplicate_key_across_files(tmp_path: Path) -> None:
    first = _write(tmp_path / "a.yaml", "email: a@b.c\n")
    second = _write(tmp_path / "b.yaml", "email: c@d.e\n")

    with pytest.raises(
        SnippetLoadError,
        match=r"duplicate snippet 'email' in .*b\.yaml:1 \(already defined in .*a\.yaml:1\)",
    ):
        merge_snippet_files([first, second])


def test_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "email: [\n")

    with pytest.raises(SnippetLoadError, match="invalid YAML"):
        merge_snippet_files([path])


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SnippetLoadError, match="file not found"):
        merge_snippet_files([tmp_path / "missing.yaml"])


def test_rejects_non_utf8(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(SnippetLoadError, match="not valid UTF-8"):
        merge_snippet_files([path])


def test_merges_directory_in_name_order(tmp_path: Path) -> None:
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    _write(snippets / "b.yaml", "beta: two\n")
    _write(snippets / "a.yaml", "alpha: one\n")

    assert list(load_directory(snippets)) == ["alpha", "beta"]


def test_directory_errors(tmp_path: Path) -> None:
    missing = tmp_path / "snippets"
    with pytest.raises(FileAccessError, match="folder not found"):
        load_directory(missing)


def test_load_directory_accepts_empty_directory(tmp_path: Path) -> None:
    """GIVEN an existing empty folder -> WHEN loaded -> THEN return an empty mapping."""
    empty = tmp_path / "empty"
    empty.mkdir()

    assert load_directory(empty) == {}


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

    assert load_user_snippets(Path("~/custom-app")) == {"email": "user@example.com"}


def test_load_user_snippets_reports_missing_extra_path(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "extra_paths:\n  - missing.yaml\n")

    with pytest.raises(ConfigurationError, match="missing.yaml: not found"):
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

    with pytest.raises(ConfigurationError, match="extra_paths must be a list of paths"):
        load_user_snippets(app_dir)


def test_config_rejects_non_string_extra_path(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "extra_paths:\n  - true\n")

    with pytest.raises(ConfigurationError, match="extra_paths item 1 must be a path"):
        load_user_snippets(app_dir)


def test_config_rejects_non_string_hotkey(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "hotkey: 123\n")

    with pytest.raises(ConfigurationError, match="hotkey must be a string"):
        load_user_snippets(app_dir)


def test_config_rejects_unknown_setting(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    (app_dir / "snippets").mkdir(parents=True)
    _write(app_dir / "config.yaml", "unexpected: value\n")

    with pytest.raises(ConfigurationError, match="unknown setting 'unexpected'"):
        load_user_snippets(app_dir)


def test_hotkey_accepts_supported_chords() -> None:
    check_hotkey("Ctrl+Shift+Space")
    check_hotkey("ctrl+k+s")
    check_hotkey("ALT + F12")


@pytest.mark.parametrize(
    "hotkey",
    ["", "Space", "Ctrl+", "Ctrl+Unknown", "Ctrl+K+K", "Ctrl+Ctrl+K", 123],
)
def test_hotkey_rejects_malformed_chords(hotkey: object) -> None:
    with pytest.raises(InvalidHotkeyError):
        check_hotkey(hotkey)


def test_check_config_reports_all_problems_at_once(tmp_path: Path) -> None:
    """GIVEN three independent config errors -> WHEN checked -> THEN report all three."""
    config = _write(
        tmp_path / "config.yaml",
        "hotkey: Space\nextra_paths: shared\nunexpected: value\n",
    )

    result = check_configuration_file(config)

    assert len(result.problems) == 3
    assert "unknown setting 'unexpected'" in str(result.problems)
    assert "hotkey must include Ctrl" in str(result.problems)
    assert "extra_paths must be a list" in str(result.problems)


def test_check_config_stops_after_yaml_syntax_error(tmp_path: Path) -> None:
    """GIVEN invalid YAML -> WHEN checked -> THEN report syntax without structure checks."""
    config = _write(tmp_path / "config.yaml", "hotkey: [\nextra_paths: not-a-list\n")

    result = check_configuration_file(config)

    assert len(result.problems) == 1
    assert isinstance(result.problems[0], InvalidYamlSyntaxError)


def test_check_extra_paths_reports_each_invalid_path(tmp_path: Path) -> None:
    """GIVEN three invalid paths -> WHEN config is checked -> THEN report each path."""
    config = _write(tmp_path / "config.yaml", "extra_paths: [true, missing.yaml, wrong.txt]\n")
    _write(tmp_path / "wrong.txt", "not a snippet file\n")

    result = check_configuration_file(config)

    assert len(result.problems) == 3
    assert all(isinstance(problem, InvalidExtraPathError) for problem in result.problems)
    assert "item 1" in str(result.problems[0])
    assert "missing.yaml: not found" in str(result.problems[1])
    assert "expected a .yaml or .yml file" in str(result.problems[2])


def test_check_snippet_files_collects_errors_across_files(tmp_path: Path) -> None:
    """GIVEN two invalid files -> WHEN checked -> THEN report the problem in each file."""
    wrong_structure = _write(tmp_path / "structure.yaml", "- not a mapping\n")
    wrong_syntax = _write(tmp_path / "syntax.yaml", "name: [\n")

    snippets, problems = check_snippet_files([wrong_structure, wrong_syntax])

    assert snippets == {}
    assert len(problems) == 2
    messages = "\n".join(map(str, problems))
    assert str(wrong_structure) in messages
    assert str(wrong_syntax) in messages


def test_duplicate_names_report_both_locations(tmp_path: Path) -> None:
    """GIVEN duplicate names -> WHEN files are merged -> THEN report both locations."""
    first = _write(tmp_path / "first.yaml", "email: first\n")
    second = _write(tmp_path / "second.yaml", "email: second\n")

    with pytest.raises(SnippetLoadError) as exc:
        merge_snippet_files([first, second])

    duplicate = next(
        problem for problem in exc.value.problems if isinstance(problem, DuplicateSnippetError)
    )
    assert f"{first}:1" in str(duplicate)
    assert f"{second}:1" in str(duplicate)


def test_nothing_loaded_when_config_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN invalid config and valid snippets -> WHEN loading -> THEN skip snippet checks."""
    app_dir = tmp_path / "app"
    snippet_dir = app_dir / "snippets"
    snippet_dir.mkdir(parents=True)
    _write(snippet_dir / "valid.yaml", "name: value\n")
    _write(app_dir / "config.yaml", "hotkey: Space\n")
    snippet_check_called = False

    def track_snippet_check(paths: list[Path]) -> tuple[dict[str, str], tuple[Exception, ...]]:
        nonlocal snippet_check_called
        snippet_check_called = True
        return {}, ()

    monkeypatch.setattr("turbopaster.snippets.check_snippet_files", track_snippet_check)
    with pytest.raises(ConfigurationError):
        load_user_snippets(app_dir)

    assert not snippet_check_called


def test_main_prints_every_problem_and_exits_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """GIVEN two config errors -> WHEN the CLI runs -> THEN print both and exit with 1."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    _write(app_dir / "config.yaml", "hotkey: Space\nextra_paths: shared\n")

    with pytest.raises(SystemExit) as exc:
        main(["--app-dir", str(app_dir)])

    assert exc.value.code == 1
    error = capsys.readouterr().err
    assert "hotkey must include Ctrl" in error
    assert "extra_paths must be a list" in error


def test_main_prints_names_from_explicit_app_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    app_dir = tmp_path / "app"
    snippets = app_dir / "snippets"
    snippets.mkdir(parents=True)
    _write(snippets / "example.yaml", "email: user@example.com\n")

    main(["--app-dir", str(app_dir), "--list"])

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
