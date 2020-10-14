import sys
import os
from threading import Lock
from itertools import chain

from py_rpc.config import Config
from py_rpc.server import GeventServer
from py_rpc.utils import get_env
from py_rpc.utils import get_debug_flag
from py_rpc.utils import locked_cached_property
from py_rpc.utils import get_root_path
from py_rpc.utils import setupmethod
from py_rpc.ctx import RequestContext
from py_rpc.ctx import _AppCtxGlobals
from py_rpc.ctx import AppContext
from py_rpc.response import JsonResponse
from py_rpc.response import BaseResponse
from py_rpc.request import JsonRequest
from py_rpc.globals import _request_ctx_stack
from py_rpc.logging import create_logger
from py_rpc.ctx import _sentinel


class PyRpcApp:
    before_request_funcs = {}
    after_request_funcs = {}
    before_setup_funcs = []
    before_first_request_funcs = []
    teardown_appcontext_funcs = []
    teardown_request_funcs = {}
    mappers = {}
    config_class = Config
    root_path = None
    instance_path = None
    app_ctx_globals_class = _AppCtxGlobals

    default_config = {
        "ENV": "development",
        "DEBUG": True
    }

    def __init__(self,
                 import_name,
                 instance_relative=False,
                 response_class=JsonResponse,
                 request_class=JsonRequest,
                 ):
        self.import_name = import_name
        self.root_path = get_root_path(import_name=import_name)
        self.config = self.make_config(instance_relative)
        self._before_request_lock = Lock()
        self._got_first_request = False
        self.response_class = response_class
        self.request_class = request_class

    def make_config(self, instance_relative):
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        defaults = dict(self.default_config)
        defaults["ENV"] = get_env()
        defaults["DEBUG"] = get_debug_flag()
        return self.config_class(root_path, defaults)

    def app_context(self):
        return AppContext(self)

    def _is_setup_finished(self):
        return self.debug and self._got_first_request

    @property
    def debug(self):
        return self.config["DEBUG"]

    @locked_cached_property
    def logger(self):
        return create_logger(self)

    @setupmethod
    def set_request_class(self, request_class):
        self.request_class = request_class

    @setupmethod
    def before_setup(self, f):
        self.before_setup_funcs.append(f)
        return f

    @setupmethod
    def before_request(self, f):
        self.before_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def before_first_request(self, f):
        self.before_first_request_funcs.append(f)
        return f

    @setupmethod
    def after_request(self, f):
        self.after_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def teardown_appcontext(self, f):
        self.teardown_appcontext_funcs.append(f)
        return f

    @setupmethod
    def teardown_request(self, f):
        self.teardown_request_funcs.setdefault(None, []).append(f)
        return f

    @locked_cached_property
    def name(self):
        if self.import_name == "__main__":
            fn = getattr(sys.modules["__main__"], "__file__", None)
            if fn is None:
                return "__main__"
            return os.path.splitext(os.path.basename(fn))[0]
        return self.import_name

    def add_mapper(self, name, func):
        self.mappers.update({name: func})

    def request_context(self, r_data):
        return RequestContext(self, r_data)

    def preprocess_request(self):
        funcs = self.before_request_funcs.get(None, ())
        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def process_response(self, response):
        funcs = self.after_request_funcs.get(None, ())
        for handler in funcs:
            response = handler(response)
        return response

    def full_dispatch_request(self):
        self.try_trigger_before_first_request_functions()
        rv = self.preprocess_request()
        if rv is None:
            rv = self.dispatch_request()
        return self.finalize_request(rv)

    def finalize_request(self, data):
        response = self.process_response(data)
        if isinstance(response, BaseResponse):
            return response.serializer()
        else:
            response = self.response_class(data=response).serializer()
            return response

    def try_trigger_before_first_request_functions(self):
        if self._got_first_request:
            return
        with self._before_request_lock:
            if self._got_first_request:
                return
            for func in self.before_first_request_funcs:
                func()
            self._got_first_request = True

    def dispatch_request(self):
        req = _request_ctx_stack.top.request
        func_name = req.get_call_func_name()
        params = req.get_call_func_params()
        if func_name not in self.mappers.keys():
            raise KeyError(f"{func_name} not in mappers")
        return self.mappers[func_name](**params)

    def do_call(self, r_data):
        ctx = self.request_context(r_data)
        error = None
        try:
            try:
                ctx.push()
                r = self.full_dispatch_request()
            except Exception:
                raise
            except:  # noqa: B001
                error = sys.exc_info()[1]
                raise
            return r
        finally:
            ctx.auto_pop(error)

    def do_teardown_appcontext(self, exc=_sentinel):
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        for func in reversed(self.teardown_appcontext_funcs):
            func(exc)

    def do_teardown_request(self, exc=_sentinel):
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        funcs = reversed(self.teardown_request_funcs.get(None, ()))
        for func in funcs:
            func(exc)

    def run(self, server_cls=GeventServer, host="localhost", port=5000):
        s = server_cls(host=host, port=port)
        for func in self.before_setup_funcs:
            func()
        s.run(app=self)
