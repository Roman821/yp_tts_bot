from pathlib import Path
from os import environ
from typing import Callable

from dotenv import load_dotenv


class Settings:

    LOGS_DIR = Path(__file__).resolve().parent / 'logs'
    LOGS_DIR.mkdir(exist_ok=True)

    WARNING_LOG_FILE_PATH = LOGS_DIR / 'warning.log'

    CHARACTER_LIMIT_BY_USER = 2500
    REQUEST_MAX_CHARACTERS = 500


def set_up_env_var(env_var_name: str, error_log_function: Callable) -> str | None:

    load_dotenv()

    result = environ.get(env_var_name)

    if not result:

        error_log_function(f'{env_var_name} environment variable is not set!')

        return None

    return result
