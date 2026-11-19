
import math
import os
from pathlib import Path
from typing import Callable, TypeVar

from dotenv import dotenv_values

Number = TypeVar("Number", int, float)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_environment() -> dict[str, str | None]:
    values = {
        **dotenv_values(PROJECT_ROOT / ".env.example"),
        **dotenv_values(PROJECT_ROOT / ".env"),
    }
    values.update({
        key: value for key, value in os.environ.items()
        if key.startswith("MESA_")
    })
    return values


def positive_number(
    values: dict[str, str | None], key: str, convert: Callable[[str], Number],
) -> Number:
    try:
        raw_value = values[key]
        if raw_value is None:
            raise ValueError
        value = convert(raw_value)
        if not math.isfinite(value) or not 0 < value < 100000:
            raise ValueError
        return value
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError(f"Configuração inválida: {key}") from None
