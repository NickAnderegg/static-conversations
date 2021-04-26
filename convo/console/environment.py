import os, sys
from datetime import datetime
from functools import partialmethod
from pathlib import Path
from pprint import pprint

import click
from loguru import logger

from ..config import ConvoConfig


config = {
    "handlers": [],
    "levels": [
        {"name": "VERBOSE2", "no": 22},
        {"name": "VERBOSE", "no": 23},
        {"name": "STATUS", "no": 27},
    ],
}
logger.configure(**config)
logger.__class__.status = partialmethod(logger.__class__.log, "STATUS")
logger.__class__.verbose = partialmethod(logger.__class__.log, "VERBOSE")
logger.__class__.verbose2 = partialmethod(logger.__class__.log, "VERBOSE2")


class Environment:
    _verbosity_levels = {
        -3: 1000,  # Nothing
        -2: 50,  # Critical
        -1: 30,  # Warning
        0: 27,  # Status
        1: 23,  # Verbose
        2: 22,  # Verbose2
        3: 20,  # Info
        4: 10,  # Debug
        5: 5,  # Trace
    }

    # _logger = logger.bind(specific=True, name="convo-cli")
    _logger = logger
    _stdin = None

    def __init__(self):
        self._verbosity = 0
        self._quietness = 0
        self._log_level = self._verbosity_levels[0]
        self.home = os.getcwd()
        self._stdin = ""
        self.config = None

        self._stdout_handler = self._logger.add(
            sys.stdout,
            level=0,  # Log level determination is handled by `filter_stdout()` method
            filter=self.filter_stdout,
            format=self.format_logging,
        )

        self._stderr_handler = self._logger.add(
            sys.stderr,
            level=0,
            filter=self.filter_stderr,
            format=self.format_logging,
        )

    @staticmethod
    def get_env(key, default=None):
        Environment._logger.trace(
            "Loading value from environment variable `{}`...", key
        )

        env_value = os.getenv(key, default=default)
        if env_value is default:
            Environment._logger.trace(
                "\t- Value for `{}` not set; returning default.", key
            )
        else:
            Environment._logger.trace("\t- Value for `{}` found.", key)

        return os.getenv(key, default)

    def filter_stdout(self, kwargs):
        level = kwargs["level"].no

        if level >= 30:
            return False

        if level >= self._log_level:
            return kwargs
        else:
            return False

    def filter_stderr(self, kwargs):
        level = kwargs["level"].no

        if level < 30:
            return False

        if level >= self._log_level:
            return kwargs
        else:
            return False

    def format_logging(self, kwargs):
        message_level = kwargs["level"].no

        message = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:"
            "<cyan>{line}</cyan> - <level>{message}</level>\n"
        )

        if self.quietness:
            message = "{level: <8} | {name}:{function}:{line} - {message}\n"

        if message_level == 27:
            message = "{message}\n"
        elif message_level < 30:
            if self.verbosity < 2:
                message = "<level>{level: <8}</level> | <cyan>{name}</cyan>: <level>{message}</level>\n"

        if self.verbosity >= 4 and "name" in kwargs["extra"]:
            message = "".join([kwargs["extra"]["name"], ": ", message])

        return message.format(**kwargs)

    def add_trace_log(self, dir_path):
        path = Path(dir_path).resolve()
        path.mkdir(exist_ok=True, parents=True)

        path = path / f"convo-cli_{datetime.now().isoformat()}.log"

        self._tracelog_handler = self._logger.add(
            path,
            level=0,
        )

    @property
    def quietness(self):
        return self._quietness

    @quietness.setter
    def quietness(self, value):
        if value > 0:
            del self.verbosity
        else:
            self._quietness = 0
            return

        if value > 3:
            value = 3
        self._quietness = value
        self._log_level = self._verbosity_levels[-1 * value]

        self.debug("Set quietness level to {}.", self._quietness)
        self.debug("Set log level to {}.", self._log_level)

    @quietness.deleter
    def quietness(self):
        self._quietness = 0

    @property
    def verbosity(self):
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value):
        if self.quietness:
            return
        if value > 5:
            value = 5
        self._verbosity = value
        self._log_level = self._verbosity_levels[value]

        self.debug("Set verbosity level to {}.", self._verbosity)
        self.debug("Set log level to {}.", self._log_level)

    @verbosity.deleter
    def verbosity(self):
        self._verbosity = 0

    def __getattr__(self, name):
        if hasattr(self._logger, name):
            return getattr(self._logger, name)

    def _log(self, level, msg, *args):
        if args:
            msg = msg.format(*args)

        self._logger.log(
            self._verbosity_levels[level],
            msg,
        )

    def log(self, msg, *args):
        self._log(0, msg, *args)

    def vlog(self, msg, *args):
        self._log(1, msg, *args)

    def vvlog(self, msg, *args):
        self._log(2, msg, *args)

    def vvvlog(self, msg, *args):
        self._log(3, msg, *args)


pass_environment = click.make_pass_decorator(Environment, ensure=True)
