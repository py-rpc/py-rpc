import os


def get_env():
    return os.environ.get("PY_RPC_ENV", "development")


def get_debug_flag():
    val = os.environ.get("PY_RPC_DEBUG")
    if not val:
        return get_env() == "development"

    return val.lower() not in ("0", "false", "no")
