
import shlex

from .client import run_adb


def open_browser(transport_id: str, url: str) -> bool:
    intent = (
        "shell", "am", "start", "-W", "-a", "android.intent.action.VIEW",
        "-c", "android.intent.category.BROWSABLE", "-d", shlex.quote(url),
    )
    
    for browser in (("-p", "com.android.chrome"), ()):
        try:
            if "Status: ok" in run_adb("-t", transport_id, *intent, *browser):
                return True
        except RuntimeError:
            continue
    return False
