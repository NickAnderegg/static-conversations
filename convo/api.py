import sys
from pprint import pprint

import requests

from .. import __version__

from . import user


class GitHubAPI(object):

    BASE_USER_AGENT = f"StaticConversations/{__version__}"
    BASE_PATH = "https://api.github.com"

    ACCEPT = "application/vnd.github.v3+json"

    def __init__(self, credentials):
        self.USER_AGENT = self.build_user_agent()

        self.auth_username, self.auth_token = credentials

        self.session = requests.Session()

        # user.User.set_api(self)

        # self.users.get_user("nickanderegg")
        # pprint(self)
        # pprint(self.users.__dict__)

        self.nods = {}
        self.users = {}

        self.get_user("nickanderegg")

    def build_headers(self):
        return {
            "Accept": self.ACCEPT,
            "User-Agent": self.build_user_agent(),
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"token {self.auth_token}",
        }

    def build_get_request(self, path, params={}):
        request_path = f"{self.BASE_PATH}{path}"

        request = requests.Request(
            method="GET",
            url=request_path,
            params=params,
            headers=self.build_headers(),
            auth=(self.auth_username, self.auth_token),
        )

        return request.prepare()

    @classmethod
    def build_user_agent(cls):
        ua = f"{cls.BASE_USER_AGENT} ({sys.platform})"

        return ua

    def send(self, request):
        resp = self.session.send(request)
        return resp.json()

    def get_user(self, username):
        request = self.build_get_request(f"/users/{username}")
        resp = self.send(request)

        record = user.UserRecord(resp)
        pprint(record)
        pprint(record.record)

        record.insert_records(self.users)

        pprint(self.users)
