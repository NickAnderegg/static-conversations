import os, sys
from functools import partialmethod
from pathlib import Path
from pprint import pprint

import click

CURRENT_FILE = Path(__file__).resolve()
cmd_folder = CURRENT_FILE.parent / "commands"


class CLILoader(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in cmd_folder.iterdir():
            if filename.suffix == ".py" and filename != CURRENT_FILE:
                rv.append(filename.stem)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        full_name = f"convo.console.commands.{name}"
        try:
            mod = __import__(full_name, None, None, ["cli"])
        except ImportError:
            print(sys.exc_info()[1])
            return
        return mod.cli
