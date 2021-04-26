import sys, os
from enum import Enum
from pprint import pprint

from .. import pass_environment
from ...api import GitHubAPI

import click


helptext_load_lines = [
    "Load and extract comments from repo issues.",
]
helptext_load = "\n\n".join(helptext_load_lines)


@click.command(name="load", help=helptext_load)
@pass_environment
def cli(ctx):
    ctx.manager.load_comments()
