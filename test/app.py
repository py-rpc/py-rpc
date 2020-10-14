from py_rpc.app import PyRpcApp


def first_call_func_1():
    print("first_call_func_1")


def first_call_func_2():
    print("first_call_func_2")


def func1(*args, **kwargs):
    print(args)
    print(kwargs)


if __name__ == '__main__':
    app = PyRpcApp(__name__)
    app.config.from_object("test_settings")
    print(app.config.items())
    app.before_setup(f=first_call_func_1)
    app.before_setup(f=first_call_func_2)
    app.add_mapper("test_func", func1)
    app.run()
