from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent

from turbopaster.search import create_search_window, filter_snippet_names, preview_value
from turbopaster.snippets import load_user_snippets


def test_filter_snippet_names_matches_case_insensitive_substrings() -> None:
    snippets = {
        "My Email": "email text",
        "email footer": "footer text",
        "pin": "1234",
    }

    assert filter_snippet_names(snippets, "EMAIL") == ["email footer", "My Email"]


def test_filter_snippet_names_returns_no_names_for_empty_query() -> None:
    snippets = {"zeta": "z", "Alpha": "a", "beta": "b"}

    assert filter_snippet_names(snippets, "") == []


def test_preview_escapes_multiline_values() -> None:
    assert preview_value("first line\r\nsecond line\rthird line") == (
        r"first line\nsecond line\nthird line"
    )


def test_search_palette_reveals_and_updates_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app, engine, component, _controller, window = create_search_window(
        {"Email reply": "reply", "Email signature": "signature", "Address": "address"}
    )
    window.setProperty("animationsEnabled", False)
    search_input = window.findChild(QObject, "searchInput")
    results_panel = window.findChild(QObject, "resultsPanel")
    results_list = window.findChild(QObject, "resultsList")

    assert search_input is not None
    assert results_panel is not None
    assert results_list is not None
    assert results_list.property("count") == 0
    assert results_panel.property("height") == 0

    search_input.setProperty("text", "email")
    app.processEvents()

    assert results_list.property("count") == 2
    assert results_panel.property("height") > 0
    window.close()
    component.deleteLater()
    engine.deleteLater()


def test_palette_focus_preview_and_selected_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app, engine, component, controller, window = create_search_window(
        {"Email reply": "first line\nsecond line", "Address": "somewhere"}
    )
    window.setProperty("animationsEnabled", False)
    search_input = window.findChild(QObject, "searchInput")
    results_list = window.findChild(QObject, "resultsList")
    assert search_input is not None
    assert results_list is not None

    window.requestActivate()
    app.processEvents()
    assert search_input.property("activeFocus") is True

    search_input.setProperty("text", "email")
    app.processEvents()
    current_item = results_list.property("currentItem")
    assert current_item is not None
    preview = current_item.findChild(QObject, "previewText")
    assert preview is not None
    assert preview.property("text") == r"first line\nsecond line"

    controller.choose("Email reply")
    assert controller.selected_value == "first line\nsecond line"
    window.close()
    component.deleteLater()
    engine.deleteLater()


def test_loaded_snippets_appear_in_search_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN a YAML snippet -> WHEN loaded and searched in QML -> THEN show its result."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app_dir = tmp_path / "app"
    snippets_dir = app_dir / "snippets"
    snippets_dir.mkdir(parents=True)
    (snippets_dir / "example.yaml").write_text(
        "email: user@example.com\nsig: signature\nlinked: example\n",
        encoding="utf-8",
    )
    snippets = load_user_snippets(app_dir)
    app, engine, component, _controller, window = create_search_window(snippets)
    window.setProperty("animationsEnabled", False)
    search_input = window.findChild(QObject, "searchInput")
    results_list = window.findChild(QObject, "resultsList")

    try:
        assert search_input is not None
        assert results_list is not None
        window.requestActivate()
        app.processEvents()
        assert search_input.property("activeFocus") is True
        for character in "email":
            key_event = QKeyEvent(
                QEvent.Type.KeyPress,
                ord(character.upper()),
                Qt.KeyboardModifier.NoModifier,
                character,
            )
            QCoreApplication.sendEvent(window, key_event)
        app.processEvents()

        assert results_list.property("count") == 1
        current_item = results_list.property("currentItem")
        assert current_item is not None
        preview = current_item.findChild(QObject, "previewText")
        assert preview is not None
        assert preview.property("text") == "user@example.com"
    finally:
        window.close()
        component.deleteLater()
        engine.deleteLater()
        app.processEvents()


def test_filter_snippet_names_returns_no_names_without_match() -> None:
    snippets = {"email": "email text"}

    assert filter_snippet_names(snippets, "signature") == []


def test_filter_snippet_names_sorts_results_alphabetically() -> None:
    snippets = {"zeta-email": "z", "Alpha-email": "a", "beta-email": "b"}

    assert filter_snippet_names(snippets, "email") == [
        "Alpha-email",
        "beta-email",
        "zeta-email",
    ]
