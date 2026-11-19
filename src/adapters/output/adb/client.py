
import os
import subprocess
from contextlib import contextmanager
from typing import Iterator


def _environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("ADB_SERVER_SOCKET", "ANDROID_ADB_SERVER_ADDRESS",
                "ANDROID_ADB_SERVER_PORT", "ADB_TRACE"):
        env.pop(key, None)
    return env


def run_adb(*args: str) -> str:
    try:
        result = subprocess.run(
            ["adb", *args], check=True, capture_output=True,
            text=True, errors="replace", env=_environment(), timeout=5,
        )
    except FileNotFoundError:
        raise RuntimeError("Instale o ADB para usar a conexão USB.") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError("ADB demorou a responder. Verifique o cabo e a autorização.") from None
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr.strip() or "Falha no ADB.") from None
    return result.stdout.strip()


@contextmanager
def watch_disconnect(transport_id: str) -> Iterator[subprocess.Popen]:
    with subprocess.Popen(
        ["adb", "-t", transport_id, "wait-for-usb-disconnect"], env=_environment(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) as process:
        try:
            yield process
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
