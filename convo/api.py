import sys
from pprint import pprint

import requests

from .__version__ import __version__


class GitHubAPI(object):

    BASE_USER_AGENT = f"StaticConversations/{__version__}"
    BASE_PATH = "https://api.github.com"
    UNIVERSAL_KEYS = {
        "id",
        "node_id",
        "html_url",
        "user",
        "created_at",
        "updated_at",
    }

    def __init__(self, /, credentials):

        self.credentials = credentials
        self.repo = credentials["repo"]

        self.session = requests.Session()

        self.nodes = {}
        self.users = {}
        self.issues = {}
        self.issue_comments = {}

    def build_headers(self):
        return {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"{self.BASE_USER_AGENT} ({sys.platform})",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"token {self.credentials['auth']}",
        }

    def build_get_request(self, path, params={}):
        request_path = f"{self.BASE_PATH}/{path}"

        request = requests.Request(
            method="GET",
            url=request_path,
            params=params,
            headers=self.build_headers(),
            auth=(self.credentials["user"], self.credentials["auth"]),
        )

        return request.prepare()

    def send(self, request):
        resp = self.session.send(request)
        return resp.json()

    def get_resource(self, path, params={}):
        resource_path = "/".join([str(_) for _ in path])
        request = self.build_get_request(resource_path, params=params)

        return self.send(request)

    def filter_fields(self, resp, filter_keys):
        filtered = {
            key: val
            for key, val in resp.items()
            if key in (self.UNIVERSAL_KEYS | filter_keys)
        }

        if "user" in filtered.keys():
            user = self.get_user(filtered["user"]["login"])
            filtered["user"] = user

        return filtered

    def get_issues(self, params={}):
        resp = self.get_resource(["repos", self.repo, "issues"])

        for issue in self._filter_issues(resp):
            self.nodes[issue["node_id"]] = issue
            self.issues[issue["number"]] = issue

            issue["comments"] = self.get_issue_comments(issue["number"])

        return self.issues

    def _filter_issues(self, resp):
        filter_keys = {
            "number",
            "title",
            "body",
            "labels",
            "locked",
            "active_lock_reason",
        }

        issues = []
        for issue in resp:
            # The issues endpoint returns pull requests as well, so we should
            # skip any issues that have the `pull_request` key.
            if "pull_request" in issue:
                continue

            filtered = self.filter_fields(issue, filter_keys)
            issues.append(filtered)

        return issues

    def get_user(self, username):
        if username in self.users:
            return self.users[username]

        resp = self.get_resource(["users", username])

        user = self._filter_user(resp)

        self.nodes[user["node_id"]] = user
        self.users[user["login"]] = user

        return user

    def _filter_user(self, resp):
        filter_keys = {
            "login",
            "avatar_url",
            "name",
            "bio",
        }

        return self.filter_fields(resp, filter_keys)

    def get_issue_comments(self, issue_number):
        if issue_number in self.issue_comments:
            return self.issue_comments[issue_number]

        resp = self.get_resource(
            ["repos", self.repo, "issues", issue_number, "comments"]
        )

        comments = []
        for comment in self._filter_issue_comments(resp):
            self.nodes[comment["node_id"]] = comment
            self.issue_comments[(issue_number, comment["id"])] = comment
            comments.append(comment)

        return comments

    def _filter_issue_comments(self, resp):
        filter_keys = {"body", "user", "author_association"}

        comments = []
        for comment in resp:
            filtered = self.filter_fields(comment, filter_keys)
            comments.append(filtered)

        return comments
