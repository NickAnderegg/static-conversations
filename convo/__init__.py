from copy import deepcopy
import json
from pathlib import Path
from pprint import pprint

import frontmatter

from .api import GitHubAPI
from .config import ConvoConfig


class CommentManager(object):
    def __init__(self):

        config = ConvoConfig()
        self.credentials = config.credentials

        self.working_dir = Path.cwd()
        """The workding directory from which this tool is being run."""

        self.output_dir = self.working_dir / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.api = GitHubAPI(credentials=self.credentials)

    def load_comments(self):
        print("Loading comments...")

        issues = self.api.get_issues()

        # We can just directly access `api.users` because calling the `api.get_issues()`
        # method automatically populates the `users`, `nodes`, `issues`, and
        # `issuse_comments` attributes of the GitHubAPI instance.
        users = self.api.users
        self._process_users(users)

        comments, comment_mapping = self._parse_comments(issues)

        self._render_comments(comments)

        mapping_file = self.output_dir / "comment_mapping.json"
        with mapping_file.open("w", encoding="utf-8") as f:
            json.dump(comment_mapping, f, indent=4)

    def _render_comments(self, comments):
        comments_dir = self.output_dir / "comments"
        comments_dir.mkdir(parents=True, exist_ok=True)

        for comment_id, content in comments.items():
            comment_file = comments_dir / f"{comment_id}.json"

            with comment_file.open("w", encoding="utf-8") as f:
                json.dump(content, f, indent=4)

    def _process_users(self, users):
        users_dir = self.output_dir / "commenters"
        users_dir.mkdir(parents=True, exist_ok=True)

        for username, data in users.items():
            filename = f"{username}.json"
            user_file = users_dir / filename

            with user_file.open("w", encoding="utf-8") as f:
                json.dump(data, f)

    def _parse_comments(self, comments):
        # We want to make a deep copy to prevent modifying the original data.
        comments = deepcopy(comments)

        if type(comments) is dict:
            comments = list(comments.values())

        comment_mapping = {}
        processed = {}
        for issue in comments:
            # We don't want to include the redundant user object, so we'll
            # replace that with the username of the commenter.
            issue["user"] = issue["user"]["login"]

            parent_page, body_text = self.__parse_comment_body(issue["body"])

            issue["page"] = parent_page
            issue["body"] = body_text

            issue["parent"] = 0

            if (page := issue["page"]) not in comment_mapping:
                comment_mapping[page] = []

            comment_mapping[issue["page"]].append(issue["id"])

            replies = issue["comments"]
            del issue["comments"]

            replies = self._process_replies(replies, issue["id"])

            issue["replies"] = list(replies.keys())

            processed.update(replies)
            processed[issue["id"]] = issue

        return processed, comment_mapping

    def _process_replies(self, comments, parent_comment):
        processed = {}
        for comment in comments:
            # We don't want to include the redundant user object, so we'll
            # replace that with the username of the commenter.
            comment["user"] = comment["user"]["login"]

            comment["body"] = comment["body"].replace("\r\n", "\n")
            comment["parent"] = parent_comment

            processed[comment["id"]] = comment

        return processed

    @staticmethod
    def __parse_comment_body(body):
        metadata, content = frontmatter.parse(body)
        parent_page = metadata["page"].strip("/ ")
        body_text = content.replace("\r\n", "\n")

        return parent_page, body_text
