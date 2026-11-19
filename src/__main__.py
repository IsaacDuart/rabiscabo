
from .adapters.input.cli import main
from .startup.bootstrap import run

if __name__ == "__main__":
    raise SystemExit(main(run))
