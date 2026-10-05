from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, SecretStr


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    gmail_address: str
    gmail_app_password: SecretStr
    imap_host: str = "imap.gmail.com"

    REQUIRED_VARS: ClassVar[tuple[str, ...]] = ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        load_dotenv(env_file)

        missing = [
            name for name in cls.REQUIRED_VARS if not os.getenv(name, "").strip()
        ]
        if missing:
            raise ConfigError(f"Missing required variables: {', '.join(missing)}")

        return cls(
            gmail_address=os.environ["GMAIL_ADDRESS"].strip(),
            gmail_app_password=os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""),
        )
