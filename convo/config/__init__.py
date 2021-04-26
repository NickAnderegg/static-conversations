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

        self.auth = AuthConfig(ctx, self.config_dir / "auth.yml")


class ConfigFile(object):
    def __init__(
        self,
        ctx,
        file_path: t.Union[str, Path],
        *args,
        **kwargs,
    ):
        self.ctx = ctx

        if type(file_path) is str:
            ctx.trace("Getting config file path from string: {}", file_path)
            self.file_path = Path(file_path).resolve()
        elif isinstance(file_path, Path):
            ctx.trace("Getting config file path from Path object: {}", file_path)
            self.file_path = file_path.resolve()
        else:
            ctx.critical(
                "`file_path` must be a string or pathlib.Path. Value passed: {}",
                file_path,
            )
            raise TypeError("`file_path` must be a string or pathlib.Path.")

        ctx.trace("Checking if config file at {} exists...", self.file_path)
        if not self.file_path.exists():
            ctx.trace("\tFile {} doesn't exist. Creating it.", self.file_path)
            self.file_path.touch(mode=0o600, exist_ok=False)
        else:
            ctx.trace(
                "\tFile {} exists. Ensuring correct permissions are set...",
                self.file_path,
            )
            self.file_path.touch(mode=0o600, exist_ok=True)

        with self.reader() as f:
            ctx.trace("Opening {} for reading...", self.file_path)

            self.file_content = f.read()
            self.original_length = len(self.file_content)

            ctx.trace("Length of config file: {}", self.original_length)

            self.parsed_content = yaml.load(self.file_content)

    @contextmanager
    def reader(self):
        self.ctx.trace("Opening `{}` for reading...", self.file_path)
        with self.file_path.open("r", encoding="utf-8") as f:
            yield f

    @contextmanager
    def writer(self, append=False):
        if append:
            mode = "a"
        else:
            mode = "w"

        self.ctx.trace(
            "Opening `{}` for writing with mode '{}'...", self.file_path, mode
        )
        with self.file_path.open(mode, encoding="utf-8") as f:
            yield f

    def _write_config(self):
        self.ctx.trace("Dumping config to file `{}`...", self.file_path)
        with self.writer() as f:
            yaml.dump(self.parsed_content, f)


class AuthConfig(ConfigFile):
    def __init__(
        self,
        ctx,
        file_path: t.Union[str, Path],
    ):
        super().__init__(ctx, file_path)

        self.username = None
        self.token = None

    def _set_value(self, key, value, no_save=False):
        if not no_save:
            self.parsed_content[key] = value
            self._write_config()

    def set_username(self, username, no_save=False):
        self.username = username
        self._set_value("username", username, no_save=no_save)

    def set_token(self, token, no_save=False):
        self.token = token
        self._set_value("token", token, no_save=no_save)

    def load_credentials(self):
        if self.username and self.token:
            return self.username, self.token

    def load_saved_credentials(self):
        if self.username and self.token:
            return

        self.ctx.debug("Attemping to load saved credentials...")
        if not self.parsed_content:
            self.ctx.debug("No saved credentials found. Writing default file.")
            self.parsed_content = {
                "username": "",
                "token": "",
            }
            self._write_config()

        self.username = self.parsed_content["username"]
        self.ctx.trace("Loaded username is `{}`.", self.username)

        self.token = self.parsed_content["token"]
        if not self.token:
            self.ctx.debug("No saved token found.")
        else:
            self.ctx.trace("Auth token set from saved config.")

    def process_login(self, ignore_env, stdin, username, *args, **kwargs):
        auth_username = None
        auth_token = None

        username_is_env = False
        token_is_env = False

        self.load_saved_credentials()

        if not ignore_env:
            self.ctx.trace(
                "`--ignore-env` is not set; environment variables are taking priority."
            )
            auth_username = self.ctx.get_env("GITHUB_ACTOR")
            if auth_username:
                username_is_env = True

            auth_token = self.ctx.get_env("GH_TOKEN")
            if auth_token is None:
                auth_token = self.ctx.get_env("GITHUB_TOKEN")

                if auth_token:
                    token_is_env = True
            else:
                token_is_env = True
        else:
            self.ctx.debug("`--ignore-env` is set. Ignoring environment variables.")

        if not auth_token and stdin:
            self.ctx.debug("Attempting to get auth token from stdin...")
            auth_token = self.ctx._stdin.strip()

            if auth_token:
                self.ctx.trace("\t- Non-empty value retrieved from stdin.")
            else:
                self.ctx.trace("\t- Empty value retrieved from stdin.")

        if not auth_username:
            self.ctx.trace(
                "No username found in environment variables. Checking CLI arguments."
            )
            if username:
                auth_username = username
            else:
                self.ctx.trace("No username found on command line.")

        if not auth_username:
            if not self.username:
                err_msg = (
                    "You must specify a username as an argument or an environment variable. "
                    "Run this command with `--help` for more information."
                )
                raise click.UsageError(err_msg)
            else:
                self.ctx.debug("Setting username to value loaded from saved config.")
        else:
            if self.username:
                self.ctx.debug(
                    "Overriding username `{}` from saved config with `{}`.",
                    self.config,
                    auth_username,
                )
            else:
                self.ctx.debug("Setting username to `{}`.", auth_username)

            self.set_username(auth_username, no_save=username_is_env)

        if not auth_token:
            if not self.token:
                err_msg = (
                    "You must pass an auth token to stdin (with the `--stdin` flag) or as an environment variable. "
                    "Run this command with `--help` for more information."
                )
                raise click.UsageError(err_msg)
            else:
                self.ctx.debug("Setting token to value loaded from saved config.")
        else:
            if self.token:
                self.ctx.debug("Overriding token from saved config.")
            else:
                self.ctx.debug("Setting auth token.")

            self.set_token(auth_token, no_save=token_is_env)
