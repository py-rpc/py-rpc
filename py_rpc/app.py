from py_rpc.config import Config
from py_rpc.server import GeventServer
from py_rpc.utils import get_env, get_debug_flag
import json


class PyRpcApp:
    before_call_funcs = {}
    after_call_funcs = {}
    before_setup_funcs = {}
    mappers = {}
    config_class = Config
    root_path = None
    instance_path = None

    default_config = {
        "ENV": "development",
        "DEBUG": True
    }

    def __init__(self, import_name, instance_relative=False):
        self.import_name = import_name
        self.config = self.make_config(instance_relative)

    def make_config(self, instance_relative):
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        defaults = dict(self.default_config)
        defaults["ENV"] = get_env()
        defaults["DEBUG"] = get_debug_flag()
        return self.config_class(root_path, defaults)

    def before_setup(self, f):
        self.before_setup_funcs.setdefault(None, []).append(f)
        return f

    def before_call(self, f):
        self.before_call_funcs.setdefault(None, []).append(f)
        return f

    def after_call(self, f):
        self.after_call_funcs.setdefault(None, []).append(f)
        return f

    def add_mapper(self, name, func):
        self.mappers.update({name, func})

    def do_call(self, recv_data):
        try:
            recv_json = json.loads(recv_data)
        except json.JSONDecodeError:
            import traceback
            return json.dumps({"status": 500, "msg": traceback.format_exc()})

    def run(self, server_cls=GeventServer, host="localhost", port=5000):
        s = server_cls(host=host, port=port)
        s.run(app=self)
