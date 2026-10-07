from pathlib import Path

import pytest

from turbopaster.hotkeys import convert_hotkey_to_pynput
from turbopaster.main import main


@pytest.mark.parametrize(
    ("hotkey", "expected"),
    [
        ("Ctrl+Shift+Space", "<ctrl>+<shift>+<space>"),
        ("ctrl+k+s", "<ctrl>+k+s"),
        ("Meta+PageUp", "<cmd>+<page_up>"),
        ("Alt+Escape", "<alt>+<esc>"),
    ],
)
def test_hotkey_tokens_convert_to_pynput_sequence(hotkey: str, expected: str) -> None:
    assert convert_hotkey_to_pynput(hotkey) == expected


def test_invalid_hotkey_prevents_launcher_startup(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """GIVEN an invalid configured hotkey -> WHEN startup runs -> THEN report an error."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "config.yaml").write_text("hotkey: Space\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main(["--app-dir", str(app_dir)])

    assert exc.value.code == 1
    assert "hotkey must include Ctrl" in capsys.readouterr().err
