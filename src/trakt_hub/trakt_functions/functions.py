import inspect

from ..trakt_hub import TraktHubViewer
from ..trakt_utils.type_hints import LiteralCategory, MoviesOnly, MoviesOrShows
from .wrappers import (
    is_functions_wrapper,
    query_viewer_wrapper,
    trakt_viewer_wrapper,
    validate_args_wrapper,
)


@validate_args_wrapper()
@trakt_viewer_wrapper("trending")
def get_trending(category: MoviesOrShows) -> dict:
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("popular")
def get_popular(category: MoviesOrShows) -> dict:
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("anticipated")
def get_anticipated(category: MoviesOrShows) -> dict:
    pass


@trakt_viewer_wrapper("boxoffice")
def get_boxoffice(category: MoviesOnly) -> dict:
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper(get_trending)
def is_trending(query: str, category: LiteralCategory) -> bool:
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper(get_popular)
def is_popular(query: str, category: LiteralCategory) -> bool:
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper(get_anticipated)
def is_anticipated(query: str, category: LiteralCategory) -> bool:
    pass


@validate_args_wrapper(all_args=True)
@query_viewer_wrapper
def trakt_query(query: str, category: LiteralCategory) -> dict:
    pass


def printer_(*args, **kwargs):
    return TraktHubViewer.print_contents(*args, **kwargs)


__all__ = tuple(
    k
    for k, v in globals().items()
    if all(
        (
            (k not in ("isfunction", "wraps")),
            inspect.isfunction(v),
            not any((k.startswith("_"), k.endswith("wrapper"))),
        )
    )
)
