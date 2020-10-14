import os
import sys
import pkgutil
from threading import RLock
from functools import update_wrapper

_missing = object()


def get_env():
    """
    获取环境变量
    :return: [str] 环境变量值, 默认是development
    """
    return os.environ.get("PY_RPC_ENV", "development")


def get_debug_flag():
    """
    获取调试标志位
    :return: True: 调试; False: 生产或者其他环境
    """
    val = os.environ.get("PY_RPC_DEBUG")
    if not val:
        return get_env() == "development"

    return val.lower() not in ("0", "false", "no")


def setupmethod(f):
    def wrapper_func(self, *args, **kwargs):
        if self._is_setup_finished():
            raise AssertionError(
                "A setup function was called after the "
                "first request was handled.  This usually indicates a bug "
                "in the application where a module was not imported "
                "and decorators or other functionality was called too late.\n"
                "To fix this make sure to import all your view modules, "
                "database models and everything related at a central place "
                "before the application starts serving requests."
            )
        return f(self, *args, **kwargs)

    return update_wrapper(wrapper_func, f)


class locked_cached_property:

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func
        self.lock = RLock()

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        with self.lock:
            value = obj.__dict__.get(self.__name__, _missing)
            if value is _missing:
                value = self.func(obj)
                obj.__dict__[self.__name__] = value
            return value


def get_root_path(import_name):
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, "__file__"):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Next attempt: check the loader.
    loader = pkgutil.get_loader(import_name)

    # Loader does not exist or we're referring to an unloaded main module
    # or a main module without path (interactive sessions), go with the
    # current working directory.
    if loader is None or import_name == "__main__":
        return os.getcwd()

    if hasattr(loader, "get_filename"):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, "__file__", None)

        # If we don't have a filepath it might be because we are a
        # namespace package.  In this case we pick the root path from the
        # first module that is contained in our package.
        if filepath is None:
            raise RuntimeError(
                "No root path can be found for the provided module"
                f" {import_name!r}. This can happen because the module"
                " came from an import hook that does not provide file"
                " name information or because it's a namespace package."
                " In this case the root path needs to be explicitly"
                " provided."
            )

    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))
