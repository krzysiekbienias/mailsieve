import pytest

from mailsieve.config import ConfigError, Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in Settings.REQUIRED_VARS:
        monkeypatch.delenv(name, raising=False)


def test_loads_valid_config(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "GMAIL_ADDRESS=a@gmail.com\nGMAIL_APP_PASSWORD=abcd efgh ijkl mnop\n"
    )

    settings = Settings.from_env(env)

    assert settings.gmail_address == "a@gmail.com"
    assert settings.gmail_app_password.get_secret_value() == "abcdefghijklmnop"


def test_missing_password_raises(tmp_path):
    env = tmp_path / ".env"
    env.write_text("GMAIL_ADDRESS=a@gmail.com\n")

    with pytest.raises(ConfigError, match="GMAIL_APP_PASSWORD"):
        Settings.from_env(env)
