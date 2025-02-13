import calendar
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime as dt
from pathlib import Path
from string import punctuation
from urllib.parse import urlparse
from rapidfuzz import fuzz, process

from .exceptions import CHException, ExecutorException, FileException, ParserException
from .type_hints import Any, Callable, Iterable, PathLike


def validate_path(file_path: PathLike, is_file: bool = False):
    try:
        fp = Path(file_path).resolve()
    except TypeError:
        raise FileException(
            f"The provided file path {file_path!r} is not a valid path and must be a string or a Path object."
        )
    if is_file and not fp.is_file():
        raise FileException(
            f"The provided file path \033[33m{fp!r}\033[0m is not a valid file path and must be a file."
            "\nOtherwise, disable the 'is_file' argument."
        )
    elif not any((fp.is_absolute(), fp.exists())):
        raise FileException(
            f"The provided file path \033[33m{fp!r}\033[0m is not a valid path and must be an existing path."
        )
    return fp


def clean_url(url: str):
    url_only = urlparse(url).netloc
    if not url_only:
        raise ParserException(f"The provided URL {url!r} is not a valid URL.")
    return url_only


def best_match(s: str, value: Iterable[str], extract_single: bool = True, **kwargs):
    pe = getattr(process, "extract" if not extract_single else "extractOne")
    return pe(s.lower(), (i.lower() for i in value), scorer=fuzz.ratio, **kwargs)


def soupify(contents: str, markup: str = "html.parser"):
    def _soup(*args):
        try:
            return BeautifulSoup(*args)
        except KeyError:
            raise ParserException(
                f"The provided contents {args[0]!r} is not a valid content and must be a string or a file-like object."
            )

    return _soup(contents, markup)


def popkwargs(*args, **kwargs):
    df_value = kwargs.pop("default_value", None)
    return *(kwargs.pop(k, df_value) for k in args), kwargs


def executor(func: Callable, *args, **kwargs):
    max_w, epool, kwargs = popkwargs("max_workers", "epool", **kwargs)
    if all((max_w is not None, not isinstance(max_w, int))):
        raise ExecutorException(
            f"The provided {max_w = !r} is not a valid argument and must be {None!r} or a positive integer."
        )

    _exec = [ThreadPoolExecutor, ProcessPoolExecutor][epool == "ppex"]
    yield from _exec.map(func, *args, **kwargs)


def get_datetime(increment_day: int = 0):
    _dt = dt.now()
    date, day = _dt.date(), _dt.day
    try:
        return date.replace(day=day + increment_day)
    except ValueError:
        month = calendar.month_name[date.month]
        month_range = calendar.monthrange(date.year, date.month)[1]
        raise CHException(
            f"Cannot increment the day by {increment_day} as it exceeds the month of {month} which has {month_range} days."
        )


def enumerate_at_one(obj: Any):
    return enumerate(obj, start=1)
