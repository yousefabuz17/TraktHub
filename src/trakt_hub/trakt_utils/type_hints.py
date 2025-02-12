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


PathLike = Union[str, Path]
StrTuple = tuple[str, ...]
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
