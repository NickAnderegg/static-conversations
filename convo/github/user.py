from copy import deepcopy
from pprint import pprint

from .record import APIRecord, APIRecordCache


class UserRecord(APIRecord):
    _record = {
        **APIRecord._record,
        **{
            "login": str,
            "avatar_url": str,
            "name": str,
            "email": str,
            "created_at": str,
            "two_factor_authentication": bool,
        },
    }

    _keys = frozenset([*APIRecord._keys, "login"])

    _path = [*APIRecord._path, "users", "{username}"]

    def __init__(self, response):
        self.record = self.parse_response(response)

    # @classmethod
    # def get_re(cls, username):
    #     resource_path = "/".join(cls._path)
    #     resource_path = resource_path.format(username=username)
    #     print(resource_path)

    # def __init__(self):
    #     # pass
    #     pprint(self._record)
    #     pprint(self._path)
    #     pprint(self._keys)


class User:

    API = None

    @classmethod
    def set_api(cls, api):
        cls.API = api
        cls.API.users = APIRecordCache(prototype=UserRecord, api=api)

    @classmethod
    def get_user(cls):
        endpoint = ["user"]
