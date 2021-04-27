"""Configure the Static Conversations tool.

This module reads app configuration from environment variables. The variables
currently read configure the user, authentication token, and repository.
"""

import os, sys

from contextlib import contextmanager
from copy import deepcopy
import typing as t

from pathlib import Path
from pprint import pprint

from ruamel.yaml import YAML

yaml = YAML()


class ConvoConfig(object):
    """Class for reading app configuration from environment variables."""

    def __init__(self):
        """Initialize a new ConvoConfig instance."""

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
        """A dict containing the authentication information read from
        environment variables."""

    @staticmethod
    def get_env(*keys: str, default: t.Any = None) -> t.Union[str, t.Any]:
        """Read environment variables.

        An arbitrary number of positional arguments specifying the names of
        environment variables can be passed to this method. Each variable will
        be checked in the order that it was passed to this method, and the value
        of the first set variable will be returned. If none of the passed variables
        are set, this method returns the value of the `default` keyword argument.

        Parameters
        ----------
        *keys
            One or more positional arguments that specify the environment variables
            to be read, in order of priority.
        default : None
            The value to return if none of the environment variables are set.

        Returns
        -------
        str or Any
            The value of the highest-priority environment variable that is set,
            or an arbitrary object specified by the `default` argument.
        """
        for key in keys:
            val = os.getenv(key)

            # os.getenv will return `None` if it is not set, but it can also
            # return an empty string if the environment variable has been set
            # with an empty string. Therefore, we want to check for both.
            if val is not None and val != "":
                return val

        return default
