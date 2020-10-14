from py_rpc.serializer import JsonSerializer


class BaseRequest:
    def __init__(self, r_data):
        self.r_data = r_data

    def get_call_func_name(self) -> str:
        raise NotImplemented()

    def get_call_func_params(self) -> dict:
        raise NotImplemented()


class JsonRequest(BaseRequest):

    def __init__(self, r_data):
        super(JsonRequest, self).__init__(r_data=r_data)
        self.j_data = JsonSerializer().loads(s_data=r_data)

    def get_call_func_name(self) -> str:
        return self.j_data.get("name")

    def get_call_func_params(self) -> dict:
        return self.j_data.get("param")

    @property
    def r_data(self):
        return self.r_data

    @r_data.setter
    def r_data(self, value):
        self._r_data = value
