from functools import wraps

from ..trakt_hub import TraktHub
from ..trakt_utils.exceptions import THException
from ..trakt_utils.type_hints import Callable
from ..trakt_utils.utils import best_match


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
            return TraktHub(category=cat).track_hub(get_type)

        return wrapper

    return decorator


def is_functions_wrapper(get_func: Callable):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            q, cat = (
                kwargs.get(*i) for i in (("query", args[0]), ("category", args[1]))
            )
            current_now = get_func(cat)
            titles = [i["Title"] for i in current_now.values()]
            if not (found_match := best_match(q, titles)):
                return False
            _, score, _ = found_match
            return score >= 90

        return wrapper

    return decorator


def query_viewer_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        q, cat = (kwargs.get(*i) for i in (("query", args[0]), ("category", args[1])))
        tk_hub = TraktHub(query=q, category=cat)
        if cat == "people":
            return tk_hub.track_person()
        return tk_hub.search()

    return wrapper


__all__ = tuple(k for k, v in globals().items() if k.endswith("wrapper"))
