from pprint import pprint


class APIRecordCache(object):
    def __init__(self, prototype, api):
        self._prototype = prototype
        self._records = {}
        self._api = api

    def get(self, **kwargs):
        resource_path = "/".join(self._path)
        resource_path = resource_path.format(**kwargs)
        print(resource_path)

    def __getattr__(self, name):
        if hasattr(self._prototype, name):
            print(f"Checking for attr: {name}")
            return getattr(self._prototype, name)


class APIRecord(object):
    _record = {
        "id": int,
        "node_id": str,
        "url": str,
    }

    _keys = frozenset(["node_id"])

    _path = [""]

    def parse_response(self, response):
        record = {}
        for key, val in response.items():
            if key in self._record:
                record[key] = val

        return record

    def insert_records(self, records_dict):
        for key in self._keys:
            records_dict[self.record[key]] = self
