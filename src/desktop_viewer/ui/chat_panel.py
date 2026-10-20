from __future__ import annotations

import json
import logging

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtWebEngineWidgets import QWebEngineView

from ..i18n import DEFAULT_LANGUAGE, t
from .theme import DEFAULT_THEME, Theme, get_theme

logger = logging.getLogger(__name__)

# Shown until the real chat UI is wired up. It is themed so the light/dark
# switch is meaningful before the TanStack AI front-end exists.
_PLACEHOLDER = """<!doctype html>
<html data-theme="{theme}" data-lang="{lang}"><head><meta charset="utf-8"><style>
  html, body {{ height: 100%; margin: 0; }}
  body {{
    background: {bg}; color: {fg};
    font: 14px/1.7 "Segoe UI", system-ui, sans-serif;
    display: flex; align-items: center; justify-content: center;
  }}
  .card {{
    max-width: 22rem; padding: 1.5rem 1.75rem;
    border: 1px solid {border}; border-radius: 10px;
  }}
  h1 {{ margin: 0 0 .5rem; font-size: 1rem; letter-spacing: .02em; }}
  p {{ margin: 0; color: {muted}; }}
</style></head><body>
  <div class="card">
    <h1>{title}</h1>
    <p>{body}</p>
  </div>
</body></html>"""


class ChatPanel(QWebEngineView):
    """The AI chat surface, with a theme and language that survive page loads."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme: Theme = get_theme(DEFAULT_THEME)
        self._language: str = DEFAULT_LANGUAGE
        self._chat_ui_url: QUrl | None = None
        self.loadFinished.connect(self._on_load_finished)
        self._render()

    @property
    def theme_name(self) -> str:
        return self._theme.name

    def set_theme(self, name: str) -> None:
        self._theme = get_theme(name)
        # Paint the widget itself too, so resizing never flashes the old colour.
        self.page().setBackgroundColor(QColor(self._theme.chat_background))
        self._render()

    def set_language(self, code: str) -> None:
        self._language = code
        self._render()

    def load_chat_ui(self, url: QUrl) -> None:
        """Replace the placeholder with the real chat front-end."""
        self._chat_ui_url = url
        self._render()

    def _render(self) -> None:
        self.page().setBackgroundColor(QColor(self._theme.chat_background))
        if self._chat_ui_url is None:
            self.setHtml(
                _PLACEHOLDER.format(
                    theme=self._theme.name,
                    lang=self._language,
                    bg=self._theme.chat_background,
                    fg=self._theme.chat_foreground,
                    muted=self._theme.chat_muted,
                    border=self._theme.chat_border,
                    title=t("chat_placeholder_title"),
                    body=t("chat_placeholder_body"),
                )
            )
        else:
            self.load(self._chat_ui_url)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            logger.warning("Chat panel failed to load %s", self.url().toString())
            return
        if self._chat_ui_url is not None:
            self._push_theme_to_page()
            self._push_language_to_page()

    def _push_theme_to_page(self) -> None:
        """Hand the theme to the chat front-end via a data attribute.

        The front-end is expected to key its CSS off ``[data-theme=...]``.
        """
        name = json.dumps(self._theme.name)
        self.page().runJavaScript(
            f"document.documentElement.dataset.theme = {name};"
        )

    def _push_language_to_page(self) -> None:
        """Hand the language to the chat front-end via a data attribute.

        The front-end is expected to key its own i18n table off
        ``[data-lang=...]``.
        """
        code = json.dumps(self._language)
        self.page().runJavaScript(
            f"document.documentElement.dataset.lang = {code};"
        )
