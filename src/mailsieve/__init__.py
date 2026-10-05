from mailsieve.config import ConfigError, Settings


def main() -> None:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from None

    print(f"Config loaded for {settings.gmail_address}")
    print(f"Password: {settings.gmail_app_password}")
