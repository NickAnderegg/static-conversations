from pprint import pprint

import click

from .api import GitHubAPI
from .config import ConvoConfig


class CommentManager(object):
    def __init__(self):

        config = ConvoConfig()
        self.credentials = config.credentials

        self.api = GitHubAPI(credentials=self.credentials)

    def load_comments(self):
        print("Loading comments...")

        issues = self.api.get_issues()

        pprint(issues)
