from __future__ import annotations

# Minimal dict-based i18n: no Qt Linguist / .ts-.qm toolchain, just a lookup
# table plus a module-level "current language" switch. Good enough for a
# desktop app with a couple dozen strings; would not scale to a real product.

DEFAULT_LANGUAGE = "ja"
LANGUAGES = ("en", "ja")

# Every value here is written in English by convention (per project style);
# the "ja" entries below are the exact wording the GUI already shipped with,
# relocated here unmodified so the language switch has something to flip to.
_STRINGS: dict[str, dict[str, str]] = {
    "file_menu": {"en": "&File", "ja": "ファイル(&F)"},
    "open_ifc_action": {"en": "Open IFC File...", "ja": "IFC ファイルを開く..."},
    "quit_action": {"en": "Quit", "ja": "終了"},
    "view_menu": {"en": "&View", "ja": "表示(&V)"},
    "viewer_theme_menu": {"en": "3D View Background(&B)", "ja": "3D ビューの背景(&B)"},
    "chat_theme_menu": {"en": "AI Chat Panel(&C)", "ja": "AI チャットパネル(&C)"},
    "theme_light": {"en": "Light", "ja": "ライト"},
    "theme_dark": {"en": "Dark", "ja": "ダーク"},
    "ai_menu": {"en": "&AI", "ja": "AI(&A)"},
    "ai_settings_action": {"en": "AI Settings...", "ja": "AI 設定..."},
    "language_menu": {"en": "&Language", "ja": "言語(&L)"},
    "open_ifc_dialog_title": {"en": "Open IFC File", "ja": "IFC ファイルを開く"},
    "ifc_file_filter_label": {"en": "IFC Files", "ja": "IFC ファイル"},
    "all_files_filter_label": {"en": "All Files", "ja": "すべてのファイル"},
    "load_error_title": {"en": "Load Error", "ja": "読み込みエラー"},
    "load_error_text": {"en": "Could not load {name}.", "ja": "{name} を読み込めませんでした。"},
    "load_error_informative": {
        "en": "See the log below for details.",
        "ja": "詳細は下部のログを確認してください。",
    },
    "load_failed_status": {
        "en": "Failed to load: {name}",
        "ja": "読み込みに失敗しました: {name}",
    },
    "status_ready": {"en": "Ready", "ja": "準備完了"},
    "loading_status": {"en": "Loading {name} ...", "ja": "{name} を読み込み中..."},
    "loading_status_with_count": {
        "en": "Loading {name} ... {count} elements",
        "ja": "{name} を読み込み中... {count} 要素",
    },
    "loaded_status": {
        "en": "Loaded {name}: {count} elements",
        "ja": "{name} を読み込みました: {count} 要素",
    },
    "ai_settings_dialog_title": {"en": "AI Settings", "ja": "AI 設定"},
    "ai_settings_provider_label": {"en": "Provider:", "ja": "プロバイダー:"},
    "ai_settings_model_label": {"en": "Model:", "ja": "モデル:"},
    "ai_settings_api_key_label": {"en": "API Key:", "ja": "API キー:"},
    "ai_settings_save": {"en": "Save", "ja": "保存"},
    "ai_settings_cancel": {"en": "Cancel", "ja": "キャンセル"},
    "chat_placeholder_title": {"en": "AI Chat", "ja": "AI チャット"},
    "chat_placeholder_body": {
        "en": "The chat UI is not implemented yet. It will load into this area once ready.",
        "ja": "チャット UI は未実装です。実装後この領域に読み込まれます。",
    },
}

_current_language = DEFAULT_LANGUAGE


def set_language(code: str) -> None:
    global _current_language
    if code not in LANGUAGES:
        raise ValueError(f"Unknown language {code!r}; expected one of {LANGUAGES}")
    _current_language = code


def get_language() -> str:
    return _current_language


def t(key: str, **kwargs) -> str:
    try:
        template = _STRINGS[key][_current_language]
    except KeyError:
        raise KeyError(
            f"Missing i18n string for key={key!r} language={_current_language!r}"
        ) from None
    return template.format(**kwargs) if kwargs else template
