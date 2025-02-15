import inspect

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
    """
    Get the trending movies or shows on Trakt.tv.
    
    #### Args:
        - `category`: The category to get the trending data for.
            ~ "movies"
            ~ "shows"
    
    #### Returns:
        - A dictionary of the trending movies or shows.
    """
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("popular")
def get_popular(category: MoviesOrShows) -> dict:
    """
    Get the popular movies or shows on Trakt.tv.
    
    #### Args:
        - `category`: The category to get the popular data for.
            ~ "movies"
            ~ "shows"
    
    #### Returns:
        - A dictionary of the popular movies or shows.
    """
    pass


@validate_args_wrapper()
@trakt_viewer_wrapper("anticipated")
def get_anticipated(category: MoviesOrShows) -> dict:
    """
    Get the anticipated movies or shows on Trakt.tv.
    
    #### Args:
        - `category`: The category to get the anticipated data for.
            ~ "movies"
            ~ "shows"
    
    #### Returns:
        - A dictionary of the anticipated movies or shows.
    """
    pass


@trakt_viewer_wrapper("boxoffice")
def get_boxoffice(category: MoviesOnly) -> dict:
    """
    Get the current box office movies.
    
    #### Args:
        - `category`: The category to get the box office data for.
            ~ "movies"
    
    #### Returns:
        - A dictionary of the current box office movies.
    """
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper("trending")
def is_trending(query: str, category: LiteralCategory) -> bool:
    """
    Check if the query is trending on Trakt.tv.
    
    #### Args:
        - `query`: The query to check if it is trending.
        - `category`: The category of the query.
            ~ "movies"
            ~ "shows"
            ~ "people"
            ~ "calendars"
    
    #### Returns:
        - A boolean indicating if the query is trending.
    """
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper("popular")
def is_popular(query: str, category: LiteralCategory) -> bool:
    """
    Check if the query is popular on Trakt.tv.
    
    #### Args:
        - `query`: The query to check if it is popular.
        - `category`: The category of the query.
            ~ "movies"
            ~ "shows"
            ~ "people"
            ~ "calendars"
    
    #### Returns:
        - A boolean indicating if the query is popular.
    """
    pass


@validate_args_wrapper(all_args=True)
@is_functions_wrapper("anticipated")
def is_anticipated(query: str, category: LiteralCategory) -> bool:
    """
    Check if the query is anticipated on Trakt.tv.
    
    #### Args:
        - `query`: The query to check if it is anticipated.
        - `category`: The category of the query.
            ~ "movies"
            ~ "shows"
    
    #### Returns:
        - A boolean indicating if the query is anticipated.
    """
    pass


@validate_args_wrapper(all_args=True)
@query_viewer_wrapper
def trakt_query(query: str, category: LiteralCategory) -> dict:
    """
    Query Trakt.tv for the given query and category.
    
    #### Args:
        - `query`: The query to search for.
        - `category`: The category to search in.
            ~ "people"
            ~ "movies"
            ~ "shows"
            ~ "calendars"
    """
    pass


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
