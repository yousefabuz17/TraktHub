from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Optional,
    Type,
    Union,
)

IntOrStr = Union[int, str]
PathLike = Union[str, Path]
StrTuple = tuple[str, ...]
MoviesOnly = Literal["movies"]
MoviesOrShows = Literal["movies", "shows"]
LiteralCategory = Literal["people", "movies", "shows", "calendars"]
LiteralSection = Literal[
    "trending",
    "popular",
    "anticipated",
    "boxoffice",
    "premieres",
    "new-shows",
    "finales",
    "dvd",
]
