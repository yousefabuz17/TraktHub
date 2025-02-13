from .trakt_hub import TraktHub, TraktHubViewer
from .trakt_utils.parsers import APIParser, ConfigFileParser, _metadata_parser
from .trakt_functions import (
    get_anticipated,
    get_popular,
    get_trending,
    is_anticipated,
    is_popular,
    is_trending,
    trakt_query,
)


# pyproject.toml
_pyproject = _metadata_parser()

# Package Metadata
__license__ = f"{_pyproject['license']}, Version 2.0"
__version__, __author__, __summary__, __url__ = (
    _pyproject.get(k) for k in ("version", "author", "description", "url")
)
__copyright__ = f"Copyright © 2024, {__author__}"


__all__ = (
    "APIParser",
    "ConfigFileParser",
    "TraktHub",
    "TraktHubViewer",
    "get_anticipated",
    "get_popular",
    "get_trending",
    "is_anticipated",
    "is_popular",
    "is_trending",
    "trakt_query",
    "__license__",
    "__version__",
    "__author__",
    "__summary__",
    "__url__",
    "__copyright__",
)
