"""Module for coordinating communication with the GitHub API.

This module is the primary entry point for reading and writing data from
the GitHub API for the purpose of managing external content for a Hugo-based
repository hosted on GitHub.
"""

import sys
from pprint import pprint
import typing as t

import requests

from .__version__ import __version__


class GitHubAPI(object):
    """Class for interacting with the GitHub API."""

    BASE_USER_AGENT: str = f"StaticConversations/{__version__}"
    """String template for creating the User Agent to append to each request."""

    BASE_PATH: str = "https://api.github.com"
    """The base URL for the GitHub API."""

    UNIVERSAL_KEYS: t.Set[str] = {
        "id",
        "node_id",
        "html_url",
        "user",
        "created_at",
        "updated_at",
    }
    """Set of keys that should never be filtered out of returned objects."""

    def __init__(self, /, credentials: dict[str, str]) -> None:
        """Initialize a new GitHubAPI instance.

        Parameters
        ----------
        credentials :
            Dict of strings containing the credentials necessary to make requests
            to the GitHub API.
        """

        self.credentials: dict[str, str] = credentials
        """A dict containing the username, personal access token, and repository
        to use when making requests to the API."""

        self.repo: str = credentials["repo"]
        """The full repository name in the form `{OWNER}/{REPOSITORY}` to use when
        making requests to the API."""

        self.session: requests.Session = requests.Session()
        """The `Session()` object that sends requests to the API."""

        self.nodes: dict[str, dict] = {}
        """A dict containing the `node_id` of all objects retrieved from the API as
        the key and a dict representing the object as the value."""

        self.users: dict[str, dict] = {}
        """A dict of user objects returned by the API, indexed by username."""

        self.issues: dict[str, dict] = {}
        """Issue objects within the repository, indexed by the issue number."""

        self.issue_comments: dict[str, dict] = {}
        """A dict of all comments on issues within the repository, as returned by
        the API. The index of each object is a tuple containing the issue number
        followed by the comment number."""

        self.headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"{self.BASE_USER_AGENT} ({sys.platform})",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"token {self.credentials['auth']}",
        }
        """A dictionary of the headers that will be attached to each request."""

    def _build_get_request(self, path, params={}):
        request_path = f"{self.BASE_PATH}/{path}"

        request = requests.Request(
            method="GET",
            url=request_path,
            params=params,
            headers=self.headers,
            auth=(self.credentials["user"], self.credentials["auth"]),
        )

        return request.prepare()

    def _send(self, request):
        resp = self.session.send(request)
        return resp.json()

    def get_resource(self, path, params={}):
        resource_path = "/".join([str(_) for _ in path])
        request = self._build_get_request(resource_path, params=params)

        return self._send(request)

    def _filter_fields(
        self,
        resp: dict[str, t.Any],
        filter_keys: set,
    ) -> dict[str, t.Any]:
        """Filter keys out of object.

        This method accepts a JSON object containing data returned by the
        GitHub API and filters out any key-value pairs that aren't specified
        by the `filter_keys` parameter.

        The filter list used by this method is a union of the set `filter_keys`
        passed to the method and the class's `UNIVERSAL_KEYS` attribute.

        Additionally, if a `user` key is encountered in the `resp` parameter,
        this method will process the object and replace it with a global pointer
        to the object that resides in the class instance's `users` attribute.

        Parameters
        ----------
        resp : dict[str, t.Any]
            The raw JSON object returned by a request to the GitHub API.
        filter_keys : set
            A set of keys to include in the final filtered object.
        """

        filtered = {
            key: val
            for key, val in resp.items()
            if key in (self.UNIVERSAL_KEYS | filter_keys)
        }

        if "user" in filtered.keys():
            user = self.get_user(filtered["user"]["login"])
            filtered["user"] = user

        return filtered

    def get_issues(
        self,
        params: dict[str, str] = {},
    ) -> dict[str, t.Any]:
        """Retrieve all issues for repository.

        Parameters
        ----------
        params : dict[str, str]
            An optional dictionary of parameters to pass to the HTTP request.

        Returns
        -------
        dict[str, t.Any]
            A filtered object containing the nested data returned by the API.
        """

        resp = self.get_resource(["repos", self.repo, "issues"])

        for issue in self._filter_issues(resp):
            self.nodes[issue["node_id"]] = issue
            self.issues[issue["number"]] = issue

            issue["comments"] = self.get_issue_comments(issue["number"])

        return self.issues

    def _filter_issues(self, resp: list[dict[str, t.Any]]) -> list[dict[str, t.Any]]:
        """Utility method to parse raw response from Issues endpoint.

        This method drops any objects from the list which contain the `pull_request`
        key. This is necessary because the GitHub API v3 returns pull requests
        in addition to issues, and the pull requests must be filtered out.

        Parameters
        ----------
        resp :
            A list of raw objects to be processed, as returned by the Issues
            endpoint (`/repos/{owner}/{repo}/issues`) of the GitHub API.

        """
        filter_keys: set = {
            "number",
            "title",
            "body",
            "labels",
            "locked",
            "active_lock_reason",
        }

        issues: list[dict[str, t.Any]] = []
        for issue in resp:
            # The issues endpoint returns pull requests as well, so we should
            # skip any issues that have the `pull_request` key.
            if "pull_request" in issue:
                continue

            filtered = self._filter_fields(issue, filter_keys)
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

    def _filter_user(self, resp: dict[str, t.Any]) -> dict[str, t.Any]:
        """Utility method to parse raw response from User endpoint.

        Parameters
        ----------
        resp :
            The raw object to be processed, as returned by the User
            endpoint (`/users/{username}`) of the GitHub API.

        """
        filter_keys = {
            "login",
            "avatar_url",
            "name",
            "bio",
        }

        return self._filter_fields(resp, filter_keys)

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

    def _filter_issue_comments(
        self,
        resp: list[dict[str, t.Any]],
    ) -> list[dict[str, t.Any]]:
        """Utility method to parse raw response from Comments endpoint.

        This method drops any objects from the list which contain the `pull_request`
        key. This is necessary because the GitHub API v3 returns pull requests
        in addition to issues, and the pull requests must be filtered out.

        Parameters
        ----------
        resp :
            A list of raw objects to be processed, for a specific issue, as
            returned by the Comments endpoint (`/repos/{owner}/{repo}/issues/{issue_number}/comments`)
            of the GitHub API.

        """
        filter_keys = {"body", "user", "author_association"}

        comments = []
        for comment in resp:
            filtered = self._filter_fields(comment, filter_keys)
            comments.append(filtered)

        return comments
