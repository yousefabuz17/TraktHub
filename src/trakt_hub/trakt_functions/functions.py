from inspect import isfunction

from .wrappers import *
from ..trakt_utils.type_hints import LiteralCategory


@validate_args_wrapper()
@trakt_viewer_wrapper("trending")
def get_trending(category: LiteralCategory) -> dict:
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("popular")
def get_popular(category: LiteralCategory) -> dict:
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("anticipated")
def get_anticipated(category: LiteralCategory) -> dict:
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
def trakt_query(query: str, category: LiteralCategory):
    pass


__all__ = tuple(
    k
    for k, v in globals().items()
    if all(
        (
            (k not in ("isfunction", "wraps")),
            isfunction(v),
            not any((k.startswith("_"), k.endswith("wrapper"))),
        )
    )
)
