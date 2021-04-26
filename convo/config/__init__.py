import os, sys

from contextlib import contextmanager
from copy import deepcopy
import typing as t

from pathlib import Path
from pprint import pprint

from ruamel.yaml import YAML

yaml = YAML()


class ConvoConfig(object):
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config" / "convo"

        self.config_dir.mkdir(
            mode=0o755,
            parents=True,
            exist_ok=True,
        )

        username_vars = ["CONVO_USER", "GITHUB_ACTOR"]
        username = self.get_env(*username_vars)
        if username is None:
            vars_string = "`, `".join(username_vars)
            error_str = f"A username must be specified in one of these environment variables: `{vars_string}`"
            raise RuntimeError(error_str)

        token_vars = ["CONVO_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"]
        token = self.get_env(*token_vars)
        if token is None:
            vars_string = "`, `".join(token_vars)
            error_str = f"An auth token must be specified in one of these environment variables: `{vars_string}`"
            raise RuntimeError(error_str)

        repo_vars = ["CONVO_REPO", "GH_REPO", "GITHUB_REPOSITORY"]
        repo = self.get_env(*repo_vars)
        if repo is None:
            vars_string = "`, `".join(repo_vars)
            error_str = f"A repository must be specified in one of these environment variables: `{vars_string}`"
            raise RuntimeError(error_str)

        self.credentials = {
            "user": username,
            "auth": token,
            "repo": repo,
        }

    @staticmethod
    def get_env(*keys, default=None):
        for key in keys:
            val = os.getenv(key)
            if val is not None:
                return val

        return default
