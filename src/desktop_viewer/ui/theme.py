from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Colours shared by the 3D viewport and the chat panel."""

    name: str
    viewer_background: str
    chat_background: str
    chat_foreground: str
    chat_muted: str
    chat_border: str


LIGHT = Theme(
    name="light",
    viewer_background="#f4f4f6",
    chat_background="#ffffff",
    chat_foreground="#1b1b1f",
    chat_muted="#6b6b76",
    chat_border="#dcdce2",
)

DARK = Theme(
    name="dark",
    viewer_background="#1e1e22",
    chat_background="#17171a",
    chat_foreground="#e8e8ec",
    chat_muted="#9a9aa4",
    chat_border="#32323a",
)

THEMES: dict[str, Theme] = {LIGHT.name: LIGHT, DARK.name: DARK}
DEFAULT_THEME = LIGHT.name


def get_theme(name: str) -> Theme:
    try:
        return THEMES[name]
    except KeyError:
        raise ValueError(
            f"Unknown theme {name!r}; expected one of {sorted(THEMES)}"
        ) from None
