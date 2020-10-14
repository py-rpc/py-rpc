import json


class Serializer:

    def dumps(self, j_data):
        raise NotImplemented

    def loads(self, s_data):
        raise NotImplemented


class JsonSerializer(Serializer):

    def dumps(self, j_data):
        return json.dumps(j_data)

    def loads(self, s_data):
        return json.loads(s_data)
