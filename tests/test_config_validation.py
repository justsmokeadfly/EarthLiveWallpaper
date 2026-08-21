from config import _dict_to_config


def test_invalid_numeric_values_fall_back_to_defaults() -> None:
    defaults = _dict_to_config({})
    config = _dict_to_config(
        {
            "check_interval_hours": -1,
            "history_size": 0,
            "retry_count": -5,
            "retry_delay_seconds": -1,
            "max_cache_age_hours": 0,
            "max_cache_size_mb": -10,
        }
    )

    assert config.check_interval_hours == defaults.check_interval_hours
    assert config.history_size == defaults.history_size
    assert config.retry_count == defaults.retry_count
    assert config.retry_delay_seconds == defaults.retry_delay_seconds
    assert config.max_cache_age_hours == defaults.max_cache_age_hours
    assert config.max_cache_size_mb == defaults.max_cache_size_mb


def test_boolean_strings_are_parsed_safely() -> None:
    config = _dict_to_config({"autostart": "true", "paused": "false"})
    assert config.autostart is True
    assert config.paused is False
