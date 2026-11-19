
import argparse
import os
import sys
from typing import Callable

from src.config.settings import PROPORCAO
from src.domain.models.area import DrawingArea
from src.domain.services.drawing_area import area_from_ratio


def _parse_area(ratio: str) -> DrawingArea:
    try:
        return area_from_ratio(ratio)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def main(run: Callable[[DrawingArea], None]) -> int:
    parser = argparse.ArgumentParser(description="Use o Android como mesa digitalizadora no Linux.")
    parser.add_argument(
        "--proporcao", type=_parse_area, default=PROPORCAO, metavar="LARGURA:ALTURA",
        help=f"proporção da tela de destino (padrão: {PROPORCAO})",
    )
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("O receptor requer Linux com uinput.")
    if os.geteuid() == 0:
        parser.error("Execute com seu usuário normal. Veja as permissões no README.")
    try:
        run(args.proporcao)
    except (OSError, RuntimeError) as error:
        print(f"Mesa USB: {error}", file=sys.stderr)
        if isinstance(error, OSError) and error.filename == "/dev/uinput":
            print("Rode 'make setup' na sessão gráfica local e tente 'make run' de novo.", file=sys.stderr)
        return 1
    return 0
