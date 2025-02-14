from functools import wraps
from itertools import chain

from ..trakt_hub import TraktHub
from ..trakt_utils.exceptions import THException
from ..trakt_utils.utils import best_match, popkwargs, page_executor


def _get_args(args=("query", "category"), **kwargs):
    kwargs.update({"default_value": ""})
    return popkwargs(*args, **kwargs)


def validate_args_wrapper(all_args: bool = False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not any((args, kwargs)):
                raise THException(
                    "Function {func_name!r} requires {num_args} to be provided.".format(
                        func_name=func.__name__,
                        num_args="all arguments" if all_args else "an argument",
                    )
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def trakt_viewer_wrapper(get_func: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cat = kwargs.get("category", *args)
            if get_func == "boxoffice":
                cat = "movies"
            return page_executor(TraktHub, cat, get_func)

        return wrapper

    return decorator


def is_functions_wrapper(get_func: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            q, cat, kwargs = _get_args(*args, **kwargs)
            executed_pages = page_executor(TraktHub, cat, get_func)
            titles = [i["Title"] for i in executed_pages.values()]
            if not (found_match := best_match(q, titles)):
                return False
            _, score, _ = found_match
            return score >= 90

        return wrapper

    return decorator


def query_viewer_wrapper(__func):
    @wraps(__func)
    def wrapper(*args, **kwargs):
        q, cat, kwargs = _get_args(*args, **kwargs)
        tk_hub = TraktHub(query=q, category=cat)
        return getattr(tk_hub, ["search", "track_person"][cat == "people"])()

    return wrapper


__all__ = tuple(k for k in globals() if k.endswith("wrapper"))
