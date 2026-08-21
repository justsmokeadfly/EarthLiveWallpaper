"""Unit tests for the ui.i18n Translator."""

from __future__ import annotations

from domain.enums import Language
from ui.i18n import Translator


class TestTranslator:
    """Tests for string lookup, language switching, and fallback behavior."""

    def test_returns_russian_string_for_ru(self) -> None:
        tr = Translator(Language.RU)
        assert tr.get("button.update_now") == "Обновить сейчас"

    def test_returns_english_string_for_en(self) -> None:
        tr = Translator(Language.EN)
        assert tr.get("button.update_now") == "Update now"

    def test_set_language_switches_active_language(self) -> None:
        tr = Translator(Language.EN)
        assert tr.language == Language.EN
        tr.set_language(Language.RU)
        assert tr.language == Language.RU
        assert tr.get("button.settings") == "Настройки"

    def test_format_args_are_substituted(self) -> None:
        tr = Translator(Language.EN)
        result = tr.get("settings.invalid_value", error="bad number")
        assert "bad number" in result

    def test_unknown_key_falls_back_to_key_itself(self) -> None:
        tr = Translator(Language.RU)
        assert tr.get("this_key_does_not_exist") == "this_key_does_not_exist"

    def test_outcome_label_translates_enum_value(self) -> None:
        tr = Translator(Language.RU)
        assert tr.outcome_label("success") == "Успешно обновлено"
        tr.set_language(Language.EN)
        assert tr.outcome_label("success") == "Success"

    def test_every_key_present_in_both_languages(self) -> None:
        from ui.i18n import _STRINGS  # noqa: PLC0415 - internal test access

        en_keys = set(_STRINGS[Language.EN].keys())
        ru_keys = set(_STRINGS[Language.RU].keys())
        assert en_keys == ru_keys, (
            f"Key mismatch between languages. "
            f"Only in EN: {en_keys - ru_keys}. Only in RU: {ru_keys - en_keys}."
        )
