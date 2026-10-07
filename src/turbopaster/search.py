"""Qt Quick search palette for snippet names."""

import signal
from collections.abc import Mapping
from pathlib import Path
from types import FrameType
from typing import cast

from pynput import keyboard
from PySide6.QtCore import Property, QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle

from turbopaster.exceptions import HotkeyListenerError
from turbopaster.hotkeys import convert_hotkey_to_pynput


def filter_snippet_names(snippets: Mapping[str, str], query: str) -> list[str]:
    needle = query.casefold()
    if not needle:
        return []
    return sorted(
        (name for name in snippets if needle in name.casefold()),
        key=str.casefold,
    )


def preview_value(value: str) -> str:
    return value.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")


class _SearchController(QObject):
    resultsChanged = Signal()
    chosen = Signal()

    def __init__(self, snippets: Mapping[str, str]) -> None:
        super().__init__()
        self._snippets = snippets
        self._results: list[dict[str, str]] = []
        self.selected_value: str | None = None

    @Property(list, notify=resultsChanged)
    def results(self) -> list[dict[str, str]]:
        return self._results

    @Slot(str)
    def search(self, query: str) -> None:
        names = filter_snippet_names(self._snippets, query)
        self._results = [
            {"name": name, "preview": preview_value(self._snippets[name])} for name in names
        ]
        self.resultsChanged.emit()

    @Slot(str)
    def choose(self, name: str) -> None:
        if name in self._snippets:
            self.selected_value = self._snippets[name]
            self.chosen.emit()


class _WindowActivation(QObject):
    activation_requested = Signal()

    def __init__(self, window: QQuickWindow) -> None:
        super().__init__()
        self._window = window
        self.activation_requested.connect(
            self._activate_window,
            Qt.ConnectionType.QueuedConnection,
        )

    @Slot()
    def _activate_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.requestActivate()


def create_search_window(
    snippets: Mapping[str, str],
    *,
    initially_visible: bool = True,
    resident_mode: bool = False,
) -> tuple[
    QGuiApplication,
    QQmlApplicationEngine,
    QQmlComponent,
    _SearchController,
    QQuickWindow,
]:
    app = cast(QGuiApplication | None, QGuiApplication.instance())
    if app is None:
        QQuickStyle.setStyle("Basic")
        app = QGuiApplication([])

    engine = QQmlApplicationEngine()
    controller = _SearchController(snippets)
    qml_path = Path(__file__).with_name("search.qml")
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_path)))
    if component.isError():
        errors = "; ".join(error.toString() for error in component.errors())
        raise RuntimeError(f"Could not load search window {qml_path}: {errors}")
    root = component.createWithInitialProperties(
        {
            "searchController": controller,
            "initiallyVisible": initially_visible,
            "residentMode": resident_mode,
        }
    )
    if root is None:
        errors = "; ".join(error.toString() for error in component.errors())
        raise RuntimeError(f"Could not create search window {qml_path}: {errors}")

    window = cast(QQuickWindow, root)
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        window.setX(geometry.x() + (geometry.width() - window.width()) // 2)
        window.setY(geometry.y() + (geometry.height() - window.height()) // 2)
    if initially_visible:
        window.requestActivate()
        QTimer.singleShot(0, window.requestActivate)
    return app, engine, component, controller, window


def run_search_window(
    snippets: Mapping[str, str],
    hotkey: str | None = None,
) -> str | None:
    resident_mode = hotkey is not None
    app, _engine, _component, controller, window = create_search_window(
        snippets,
        initially_visible=not resident_mode,
        resident_mode=resident_mode,
    )
    app.setQuitOnLastWindowClosed(not resident_mode)

    listener: keyboard.GlobalHotKeys | None = None
    listener_timer: QTimer | None = None
    if hotkey is not None:
        activation = _WindowActivation(window)
        pynput_hotkey = convert_hotkey_to_pynput(hotkey)

        def request_activation() -> None:
            activation.activation_requested.emit()

        try:
            listener = keyboard.GlobalHotKeys({pynput_hotkey: request_activation})
            listener.start()
        except (OSError, RuntimeError, ValueError) as exc:
            raise HotkeyListenerError(f"Could not start hotkey {hotkey!r}: {exc}") from exc

        def stop_if_listener_exits() -> None:
            if listener is not None and not listener.is_alive():
                app.quit()

        listener_timer = QTimer(app)
        listener_timer.setInterval(250)
        listener_timer.timeout.connect(stop_if_listener_exits)
        listener_timer.start()

    previous_handler = signal.getsignal(signal.SIGINT)
    signal_timer = QTimer(app)
    signal_timer.setInterval(250)
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start()

    def quit_on_interrupt(_signal_number: int, _frame: FrameType | None) -> None:
        app.quit()

    signal.signal(signal.SIGINT, quit_on_interrupt)
    try:
        app.exec()
    finally:
        signal.signal(signal.SIGINT, previous_handler)
        signal_timer.stop()
        if listener_timer is not None:
            listener_timer.stop()
        if listener is not None:
            listener.stop()
            try:
                listener.join()
            except Exception as exc:
                raise HotkeyListenerError(f"The hotkey listener stopped: {exc}") from exc
    return controller.selected_value
