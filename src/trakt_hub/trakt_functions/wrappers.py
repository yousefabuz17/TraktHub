from functools import wraps

from ..trakt_hub import TraktHub
from ..trakt_utils.exceptions import THException
from ..trakt_utils.type_hints import Callable
from ..trakt_utils.utils import best_match


def _get_qc(*args, **kwargs):
    return (
        kwargs.get(*i)
        for i in (
            ("query", args[0] if args else ""),
            ("category", args[1] if args else ""),
        )
    )


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


def trakt_viewer_wrapper(get_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cat = kwargs.get("category", *args)
            if get_type == "boxoffice":
                cat = "movies"
            return TraktHub(category=cat).track_hub(get_type)

        return wrapper

    return decorator


def is_functions_wrapper(get_func: Callable):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            q, cat = _get_qc(*args, **kwargs)
            get_func_contents = get_func(cat)
            titles = [i["Title"] for i in get_func_contents.values()]
            if not (found_match := best_match(q, titles)):
                return False
            _, score, _ = found_match
            return score >= 90

        return wrapper

    return decorator


def query_viewer_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        q, cat = _get_qc(*args, **kwargs)
        tk_hub = TraktHub(query=q, category=cat)
        return getattr(tk_hub, ["search", "track_person"][cat == "people"])()

    return wrapper


__all__ = tuple(k for k in globals() if k.endswith("wrapper"))
