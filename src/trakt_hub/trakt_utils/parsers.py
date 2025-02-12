import asyncio
from aiohttp import ClientSession, TCPConnector
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ClientResponseError,
    ContentTypeError,
    InvalidURL,
    ServerDisconnectedError,
)
from async_lru import alru_cache
from bs4 import BeautifulSoup

from configparser import ConfigParser, ParsingError
from dataclasses import dataclass, field
from functools import cache, cached_property
from pathlib import Path

from .exceptions import (
    ConfigException,
    ConnectionException,
    FileException,
    ParserException,
)
from .type_hints import Optional, Union, PathLike
from .utils import clean_url, soupify, popkwargs, validate_path


@dataclass(unsafe_hash=True)
class ConfigFileParser:
    file_name: PathLike = "config.ini"
    section: str = ""

    _config_file_path: Path = field(init=False, repr=False, default=None)
    _full_config: Union[dict, str] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        for key, value in self.full_config.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"{self.full_config}"

    def __iter__(self):
        return iter(self.full_config.items())

    def __getitem__(self, section):
        try:
            return self._full_config[section]
        except IndexError as idxe:
            raise idxe
        except KeyError:
            raise ConfigException(
                f"The provided section {section!r} is not a valid section in the config file."
            )

    @staticmethod
    def _check_args(fp: PathLike, section: str = ""):
        valid_path = validate_path(fp, is_file=True)
        if not isinstance(section, str):
            raise FileException(
                f"The provided section {section!r} is not a valid section and must be a string."
                "\n If a section is proivided, it must be a valid section in the config file."
            )
        else:
            valid_section = section.lower()
        return valid_path, valid_section

    @cache
    def _get_config(self, *args):
        fp, section = self._check_args(*args)

        self._config_file_path = fp

        try:
            config_p = ConfigParser()
            config_p.read(fp)
        except ParsingError:
            raise ParserException(
                f"There was an error parsing the config file {fp!r}."
                "\nPlease check the file is correctly formatted."
            )

        full_config = {k.lower(): dict(v) for k, v in dict(config_p).items()}
        del full_config["default"]

        if section:
            if section not in full_config:
                raise FileException(
                    f"The provided section {section!r} is not a valid section in the config file."
                )
            elif section in full_config:
                return full_config[section]

        return full_config

    @cached_property
    def full_path(self):
        return self._config_file_path

    @cached_property
    def full_config(self):
        if self._full_config is None:
            self._full_config = self._get_config(self.file_name, self.section)
        return self._full_config


@dataclass
class APIParser:
    url: str = None
    endpoint: Optional[str] = ""
    api_key: Optional[str] = field(default=None, repr=False, kw_only=True)
    json_format: Optional[str] = field(default=False, repr=False, kw_only=True)
    rapid_api: Optional[bool] = field(default=False, repr=False, kw_only=True)
    headers: Optional[dict[str, str]] = field(default_factory=dict, kw_only=True)

    _host: str = field(init=False, repr=False, default=None)
    _soupify = staticmethod(soupify)

    def __post_init__(self):
        self.url, self.api_key, self.headers, self._host = self._validate_args()
        self._contents = None

    @classmethod
    async def url_request(cls, url: str, endpoint: str = "", **kwargs):
        _json, headers, kwargs = popkwargs("json_format", "headers", **kwargs)

        if endpoint:
            url = "/".join((url.rstrip("/"), endpoint))

        try:
            async with ClientSession(
                connector=TCPConnector(
                    ssl=False,
                    enable_cleanup_closed=True,
                    force_close=True,
                    ttl_dns_cache=300,
                ),
                raise_for_status=True,
            ) as session:
                async with session.get(url, headers=headers) as response:
                    return await cls._url_contents(response, _json)
        except (ClientResponseError, ContentTypeError) as ccre:
            raise ccre
        except (ClientConnectionError, ServerDisconnectedError):
            return await cls.url_request(url, headers=headers, json_format=_json)
        except InvalidURL:
            raise ConnectionException(
                f"The specified URL could not be found and is considered invalid.",
                f"{url!r}",
                f"\n[Note]: Many queries may need the year (YYYY) to be included.",
                f"E.g 'The Matrix 1999'",
            )

    @staticmethod
    @alru_cache
    async def _url_contents(response, json_format=False):
        contents = await getattr(response, ["text", "json"][bool(json_format)])()
        return (
            contents[0] if all((json_format, isinstance(contents, list))) else contents
        )

    def main_request(self, **kwargs):
        try:
            url_contents = asyncio.run(
                self.url_request(self.url, self.endpoint, **kwargs)
            )
        except ClientResponseError as cre:
            raise ConnectionException(
                f"An error occured while trying to find {self.url!r}."
                f"\n[Original Error]: {cre}"
            )
        return url_contents

    @classmethod
    def parse_html_contents(cls, html_contents=None):
        if any((html_contents is None, isinstance(html_contents, BeautifulSoup))):
            raise ParserException(
                f"The provided contents cannot be {None!r} nor an instance of {BeautifulSoup!r}."
            )
        return cls._soupify(html_contents)

    @staticmethod
    @cache
    def rapidapi_headers(api_key="", host=""):
        return {"x-rapidapi-key": api_key, "x-rapidapi-host": host}

    def _validate_args(self):
        url_and_apikey = self.url, self.api_key
        headers = self.headers
        host = clean_url(url_and_apikey[0])

        if all((*url_and_apikey,)):
            if not any((*map(lambda x: isinstance(x, str), url_and_apikey),)):
                raise ParserException(
                    f"Both the endpoint and api-key must be strings and cannot be empty."
                )

        if self.rapid_api:
            self.json_format = True
            headers = self.rapidapi_headers(url_and_apikey[1], host)

        return *url_and_apikey, headers, host

    @cached_property
    def contents(self):
        if self._contents is None:
            self._contents = self.main_request(
                json_format=self.json_format, headers=self.headers
            )
        return self._contents


__all__ = ("APIParser", "ConfigFileParser")
