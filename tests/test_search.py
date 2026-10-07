import signal
from collections.abc import Callable, Mapping
from pathlib import Path
from threading import Thread

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from turbopaster.main import main
from turbopaster.search import (
    _WindowActivation,
    create_search_window,
    filter_snippet_names,
    preview_value,
    run_search_window,
)
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


def test_search_event_loop_exits_on_sigint(monkeypatch: pytest.MonkeyPatch) -> None:
    """GIVEN the search loop is active -> WHEN SIGINT arrives -> THEN exit and restore handler."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    previous_handler = signal.getsignal(signal.SIGINT)
    QTimer.singleShot(0, lambda: signal.raise_signal(signal.SIGINT))

    assert run_search_window({}) is None
    assert signal.getsignal(signal.SIGINT) is previous_handler


def test_hotkey_activation_from_worker_thread_shows_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN a hidden palette -> WHEN a worker requests activation -> THEN show it on Qt."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app, engine, component, _controller, window = create_search_window(
        {}, initially_visible=False, resident_mode=True
    )
    activation = _WindowActivation(window)

    try:
        worker = Thread(target=activation.activation_requested.emit)
        worker.start()
        worker.join()
        app.processEvents()

        assert window.isVisible()
    finally:
        window.close()
        component.deleteLater()
        engine.deleteLater()
        app.processEvents()


def test_launcher_searches_loaded_snippets_after_hotkey(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """GIVEN snippet YAML -> WHEN hotkey opens QML search -> THEN select the loaded snippet."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app_dir = tmp_path / "app"
    snippets_dir = app_dir / "snippets"
    snippets_dir.mkdir(parents=True)
    (snippets_dir / "example.yaml").write_text("email: user@example.com\n", encoding="utf-8")
    (app_dir / "config.yaml").write_text("hotkey: Ctrl+Shift+Space\n", encoding="utf-8")
    import turbopaster.search as search_module

    state: dict[str, object] = {}

    class FakeGlobalHotKeys:
        def __init__(self, hotkeys: dict[str, Callable[[], None]]) -> None:
            self._callback = next(iter(hotkeys.values()))
            self._running = False

        def start(self) -> None:
            self._running = True
            QTimer.singleShot(0, self._callback)

        def is_alive(self) -> bool:
            return self._running

        def stop(self) -> None:
            self._running = False

        def join(self) -> None:
            return None

    create_window = search_module.create_search_window

    def create_test_window(
        snippets: Mapping[str, str],
        *,
        initially_visible: bool = True,
        resident_mode: bool = False,
    ) -> tuple[
        QGuiApplication,
        QQmlApplicationEngine,
        QQmlComponent,
        search_module._SearchController,
        QQuickWindow,
    ]:
        result = create_window(
            snippets,
            initially_visible=initially_visible,
            resident_mode=resident_mode,
        )
        app, _engine, _component, controller, window = result
        state["app"] = app
        search_input = window.findChild(QObject, "searchInput")
        results_list = window.findChild(QObject, "resultsList")
        assert search_input is not None
        assert results_list is not None

        def search_loaded_snippet() -> None:
            search_input.setProperty("text", "email")
            app.processEvents()
            state["result_count"] = results_list.property("count")
            current_item = results_list.property("currentItem")
            assert isinstance(current_item, QObject)
            preview = current_item.findChild(QObject, "previewText")
            assert preview is not None
            state["preview"] = preview.property("text")

        QTimer.singleShot(50, search_loaded_snippet)
        QTimer.singleShot(100, lambda: controller.choose("email"))
        QTimer.singleShot(150, app.quit)
        return result

    monkeypatch.setattr(search_module.keyboard, "GlobalHotKeys", FakeGlobalHotKeys)
    monkeypatch.setattr(search_module, "create_search_window", create_test_window)

    main(["--app-dir", str(app_dir)])

    assert state["result_count"] == 1
    assert state["preview"] == "user@example.com"
    assert capsys.readouterr().out.strip() == "user@example.com"


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
