import sys, os
from enum import Enum
from pprint import pprint

from . import pass_environment
from ..github import GitHubAPI

import click


# class AuthCLI(click.Group):
#     def __init__(self, *args, **kwargs):
#         super().__init__(name="auth", *args, **kwargs)

#         self.add_command(self.login)


@click.group(name="auth")
@pass_environment
def cli(ctx):
    pass


login_help_lines = [
    "Perform initial authentication for the CLI.",
    (
        "An authentication token for GitHub can be specified through the `GH_TOKEN` or `GITHUB_TOKEN` "
        "environment variables. This is the preferred method of authentication. "
        "An authentication token can also be provided through the standard input if the `--stdin` flag "
        "is set."
    ),
    (
        "The USERNAME argument is the username that you use to authenticate with GitHub. "
        "This argument must be specified if the `GITHUB_ACTOR` environment variable isn't specified."
    ),
    (
        "The environment variables for the authentication token and username will ALWAYS be used "
        "if set, unless the `--ignore-env` flag is set."
    ),
]
helptext_login = "\n\n".join(login_help_lines)


@click.command(help=helptext_login)
@click.option(
    "--ignore-env",
    "ignore_env",
    default=False,
    is_flag=True,
)
@click.option("--stdin", is_flag=True, default=False, is_eager=True)
@click.argument(
    "username",
    envvar="GITHUB_ACTOR",
    required=False,
    type=click.STRING,
)
@pass_environment
def login(ctx, ignore_env, stdin, username, *args, **kwargs):
    ctx.config.auth.process_login(ignore_env, stdin, username, *args, **kwargs)
    GitHubAPI(credentials=ctx.config.auth.load_credentials())


cli.add_command(login)
# github_auth = GitHubAuth()
# github_auth.auth.add_command(github_auth.login)
