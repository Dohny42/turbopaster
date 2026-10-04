"""Qt Quick search palette for snippet names."""

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle


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


def _create_search_window(
    snippets: Mapping[str, str],
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
    root = component.createWithInitialProperties({"searchController": controller})
    if root is None:
        errors = "; ".join(error.toString() for error in component.errors())
        raise RuntimeError(f"Could not create search window {qml_path}: {errors}")

    window = cast(QQuickWindow, root)
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        window.setX(geometry.x() + (geometry.width() - window.width()) // 2)
        window.setY(geometry.y() + (geometry.height() - window.height()) // 2)
    window.requestActivate()
    QTimer.singleShot(0, window.requestActivate)
    return app, engine, component, controller, window


def run_search_window(snippets: Mapping[str, str]) -> str | None:
    app, _engine, _component, controller, _window = _create_search_window(snippets)
    app.exec()
    return controller.selected_value
