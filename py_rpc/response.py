from py_rpc.globals import current_app
from py_rpc.serializer import JsonSerializer


class BaseResponse:

    def __init__(self, data):
        self.data = data

    def serializer(self) -> str:
        raise NotImplemented


class JsonResponse(BaseResponse):

    def serializer(self):
        return JsonSerializer().dumps(self.data)
