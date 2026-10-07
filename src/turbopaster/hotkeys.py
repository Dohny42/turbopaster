_MODIFIER_NAMES = {
    "ctrl": "ctrl",
    "shift": "shift",
    "alt": "alt",
    "meta": "cmd",
}
_KEY_NAMES = {
    "escape": "esc",
    "pagedown": "page_down",
    "pageup": "page_up",
}


def convert_hotkey_to_pynput(hotkey: str) -> str:
    tokens = [token.strip().casefold() for token in hotkey.split("+")]
    converted: list[str] = []
    for token in tokens:
        name = _MODIFIER_NAMES.get(token, _KEY_NAMES.get(token, token))
        converted.append(name if len(name) == 1 else f"<{name}>")
    return "+".join(converted)
