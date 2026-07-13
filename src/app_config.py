import os


LOCAL_MODE = "local"
CLOUD_MODE = "cloud"
APP_MODE_ENV = "APP_MODE"
VALID_MODES = {LOCAL_MODE, CLOUD_MODE}


def get_app_mode():
    mode = os.getenv(APP_MODE_ENV, LOCAL_MODE).strip().lower()
    if mode not in VALID_MODES:
        return LOCAL_MODE
    return mode


def is_local_mode():
    return get_app_mode() == LOCAL_MODE


def is_cloud_mode():
    return get_app_mode() == CLOUD_MODE


def get_mode_label():
    if is_cloud_mode():
        return "Cloud demo mode"
    return "Local persistent mode"
