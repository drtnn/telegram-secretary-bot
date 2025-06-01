import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    APP_DIR: str = os.path.dirname(os.path.realpath(__file__))

    CACHE_DIR_NAME: str = "__cache__"
    CACHE_DIR: str = os.path.join(os.path.dirname(APP_DIR), CACHE_DIR_NAME)

    DAYS_TO_SAVE_CONTENT: int = 30
    CRON_SECONDS_TO_DELETE_MESSAGES: int = 60 * 60

    def get_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
