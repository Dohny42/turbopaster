import pytest
from PySide6.QtCore import QObject

from turbopaster.search import _create_search_window, filter_snippet_names, preview_value


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
    app, engine, component, _controller, window = _create_search_window(
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
    app, engine, component, controller, window = _create_search_window(
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
