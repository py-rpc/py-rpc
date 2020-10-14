import sys
from functools import update_wrapper
from py_rpc.serializer import JsonSerializer

from py_rpc.globals import _app_ctx_stack
from py_rpc.globals import _request_ctx_stack

_sentinel = object()


class _AppCtxGlobals:

    def get(self, name, default=None):
        return self.__dict__.get(name, default)

    def pop(self, name, default=_sentinel):
        if default is _sentinel:
            return self.__dict__.pop(name)
        else:
            return self.__dict__.pop(name, default)

    def setdefault(self, name, default=None):
        return self.__dict__.setdefault(name, default)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __repr__(self):
        top = _app_ctx_stack.top
        if top is not None:
            return f"<flask.g of {top.app.name!r}>"
        return object.__repr__(self)


def after_this_request(f):
    _request_ctx_stack.top._after_request_functions.append(f)
    return f


def copy_current_request_context(f):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(
            "This decorator can only be used at local scopes "
            "when a request context is on the stack.  For instance within "
            "view functions."
        )
    reqctx = top.copy()

    def wrapper(*args, **kwargs):
        with reqctx:
            return f(*args, **kwargs)

    return update_wrapper(wrapper, f)


def has_request_context():
    return _request_ctx_stack.top is not None


def has_app_context():
    return _app_ctx_stack.top is not None


class AppContext:

    def __init__(self, app):
        self.app = app
        self.g = app.app_ctx_globals_class()
        self._refcnt = 0

    def push(self):
        self._refcnt += 1
        _app_ctx_stack.push(self)

    def pop(self, exc=_sentinel):
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_appcontext(exc)
        finally:
            rv = _app_ctx_stack.pop()
        assert rv is self, f"Popped wrong app context.  ({rv!r} instead of {self!r})"

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)


class RequestContext:

    def __init__(self, app, r_data, request=None):
        self.app = app
        if request is None:
            request = app.request_class(r_data=r_data)
        self.request = request
        self._implicit_app_ctx_stack = []
        self.preserved = False
        self._preserved_exc = None
        self._after_request_functions = []

    @property
    def g(self):
        return _app_ctx_stack.top.g

    @g.setter
    def g(self, value):
        _app_ctx_stack.top.g = value

    def copy(self):
        return self.__class__(
            self.app,
            r_data=self.request.r_data,
        )

    def push(self):
        top = _request_ctx_stack.top
        if top is not None and top.preserved:
            top.pop(top._preserved_exc)
        app_ctx = _app_ctx_stack.top
        if app_ctx is None or app_ctx.app != self.app:
            app_ctx = self.app.app_context()
            app_ctx.push()
            self._implicit_app_ctx_stack.append(app_ctx)
        else:
            self._implicit_app_ctx_stack.append(None)
        _request_ctx_stack.push(self)

    def pop(self, exc=_sentinel):
        app_ctx = self._implicit_app_ctx_stack.pop()

        try:
            if not self._implicit_app_ctx_stack:
                self.preserved = False
                self._preserved_exc = None
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_request(exc)

                request_close = getattr(self.request, "close", None)
                if request_close is not None:
                    request_close()
        finally:
            rv = _request_ctx_stack.pop()
            if app_ctx is not None:
                app_ctx.pop(exc)

            assert (
                    rv is self
            ), f"Popped wrong request context. ({rv!r} instead of {self!r})"

    def auto_pop(self, exc):
        if (
                exc is not None and self.app.preserve_context_on_exception
        ):
            self.preserved = True
            self._preserved_exc = exc
        else:
            self.pop(exc)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.auto_pop(exc_value)

    def __repr__(self):
        return (
            f"<{type(self).__name__} {self.request.url!r}"
            f" [{self.request.method}] of {self.app.name}>"
        )
