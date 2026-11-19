
from src.config.settings import TAMANHO_AREA
from src.domain.models.area import DrawingArea


def area_from_ratio(ratio: str) -> DrawingArea:
    try:
        width, height = map(int, ratio.split(":"))
        if not (1 <= width <= 10000 and 1 <= height <= 10000 and 0.2 <= width / height <= 5):
            raise ValueError
    except ValueError:
        raise ValueError("Use uma proporção entre 1:5 e 5:1, como 16:9.") from None

    scale = TAMANHO_AREA / max(width, height)
    return DrawingArea(round(width * scale), round(height * scale))
