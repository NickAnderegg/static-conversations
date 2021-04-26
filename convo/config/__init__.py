from contextlib import contextmanager
from copy import deepcopy
import typing as t

from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()


class ConvoConfig(object):
    def __init__(self, ctx):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config" / "convo"

        self.config_dir.mkdir(
            mode=0o755,
            parents=True,
            exist_ok=True,
        )

