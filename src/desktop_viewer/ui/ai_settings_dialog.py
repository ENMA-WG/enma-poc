from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from ..ai.settings import AiSettings, DEFAULT_MODELS, PROVIDERS, load_ai_settings, save_ai_settings
from ..i18n import t


class AiSettingsDialog(QDialog):
    """BYOK entry point: provider, model, and API key, stored via keyring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("ai_settings_dialog_title"))

        current = load_ai_settings()

        self._provider_combo = QComboBox(self)
        self._provider_combo.addItems(PROVIDERS)
        self._provider_combo.setCurrentText(current.provider)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)

        self._model_edit = QLineEdit(current.model, self)

        self._api_key_edit = QLineEdit(current.api_key or "", self)
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow(t("ai_settings_provider_label"), self._provider_combo)
        form.addRow(t("ai_settings_model_label"), self._model_edit)
        form.addRow(t("ai_settings_api_key_label"), self._api_key_edit)

        buttons = QDialogButtonBox(self)
        buttons.addButton(t("ai_settings_save"), QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(t("ai_settings_cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_provider_changed(self, provider: str) -> None:
        # Switching providers means the model/key fields below no longer
        # describe the selected one - reset them instead of leaving stale
        # values that look valid but belong to the other provider.
        self._model_edit.setText(DEFAULT_MODELS.get(provider, ""))
        self._api_key_edit.clear()

    def save(self) -> None:
        save_ai_settings(
            AiSettings(
                provider=self._provider_combo.currentText(),
                model=self._model_edit.text().strip(),
                api_key=self._api_key_edit.text().strip() or None,
            )
        )
