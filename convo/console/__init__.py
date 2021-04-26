import os, sys
from datetime import datetime
from functools import partialmethod
from pathlib import Path
from pprint import pprint

import click
from loguru import logger

from .environment import pass_environment
from .loader import CLILoader

# from ..api import GitHubAPI
# from ..config import ConvoConfig

from .. import CommentManager

CONTEXT_SETTINGS = dict(auto_envvar_prefix="CONVO")


verbosity_help = (
    "Set the verbosity of the tool output. "
    "Can be specified up to five times to increase verbosity."
)

quietness_help = (
    "Set the quietness of the tool output. "
    "Can be specified up to three times to increase quietness. "
    "The presence of this flag overrides any verbose flags."
)


@click.command(cls=CLILoader, context_settings=CONTEXT_SETTINGS)
@click.option("-v", "--verbose", "verbosity", count=True, help=verbosity_help)
@click.option("-q", "--quiet", "quietness", count=True, help=quietness_help)
@click.option(
    "--trace-log-dir",
    type=click.Path(file_okay=False, writable=True, resolve_path=True),
)
@pass_environment
def cli(ctx, verbosity, quietness, **kwargs):
    ctx.verbosity = verbosity
    ctx.quietness = quietness

    ctx.trace("Configuring logging environment...")
    if trace_log_dir := kwargs.get("trace_log_dir", None):
        ctx.add_trace_log(trace_log_dir)

    stdin_stream = click.get_text_stream("stdin")

    with stdin_stream as stdin:
        if not stdin.seekable():
            ctx._stdin = stdin.read()
        else:
            ctx._stdin = ""

    ctx.status("Initializing Static Conversations...")

    ctx.manager = CommentManager()


if __name__ == "__main__":
    cli(obj={})
