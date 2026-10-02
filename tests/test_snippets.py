from pathlib import Path

import pytest

from turbopaster.main import main
from turbopaster.snippets import SnippetError, load_directory, load_files


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


def test_example_file_loads() -> None:
    loaded = load_directory(Path("snippets"))

    assert loaded["email"] == "user@example.com"
    assert "Name" in loaded["sig"]


def test_main_reports_schema_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    _write(snippets / "bad.yaml", "pin: 1\n")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    error = capsys.readouterr().err
    assert error.startswith("turbopaster:")
    assert "pin" in error
