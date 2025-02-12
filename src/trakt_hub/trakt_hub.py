import re
from collections import OrderedDict
from functools import partial, wraps
from operator import itemgetter
from string import punctuation

from .trakt_utils.parsers import APIParser
from .trakt_utils.type_hints import (
    Literal,
    LiteralCategory,
    LiteralSection,
    Optional,
    StrTuple,
)
from .trakt_utils.exceptions import CHException, THException
from .trakt_utils.utils import BeautifulSoup, enumerate_at_one, get_datetime


class TraktHubViewer:
    __slots__ = (
        "_category",
        "_section",
        "_html_contents",
    )

    def __init__(
        self,
        category: LiteralCategory = "movies",
        section: LiteralSection = "",
        *,
        html_contents: BeautifulSoup = None,
    ):
        self._category = category
        self._section = section
        self._html_contents = html_contents

    def _th_viewer():
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                parser = func(self, *args, **kwargs)
                html_contents = parser.parse_html_contents(parser.contents)
                section = self._query if not args else args[0]
                return TraktHubViewer(
                    self._category, section, html_contents=html_contents
                ).get_contents()

            return wrapper

        return decorator

    def _find_all(self, tag: str, *, text: bool = False, strip: bool = False, **kwargs):
        tag_contents = self._html_contents.find_all(tag, **kwargs)
        if any((text, strip)):
            format_func = lambda x: x.get_text(strip=True) if strip else x.text
            return [format_func(i) for i in tag_contents]
        return tag_contents

    def _clean_contents(self):
        text_findall_func = partial(self._find_all, text=True)
        common_func = partial(text_findall_func, "div", class_="titles")
        _enum = partial(enumerate, start=1)

        def second_common_func(contents):
            pattern = re.compile(r"(\w+)(.*?)\s(\d{4})$")
            return {
                idx: {
                    "Title": match.group(1) + match.group(2),
                    "Year": int(match.group(3)),
                }
                for idx, i in _enum(contents)
                if (match := pattern.match(i))
            }

        match (self._category, self._section):
            # ^ -------------------Match Case for (Movies/Shows)----------------- ^ #
            case ("shows", "trending") | ("movies", "trending"):
                # Unclean Example: 41 people watchingSonic the Hedgehog 3 2024
                trending = common_func()
                pattern = re.compile(r"(\d+)\s+people watching(.+?)\s+(\d{4})$")
                cleaned_contents = {
                    idx: {
                        "Title": match.group(2).strip(),
                        "Watch Count": int(match.group(1)),
                        "Year": int(match.group(3)),
                    }
                    for idx, i in _enum(trending)
                    if (match := pattern.match(i))
                }

            case ("shows", "popular") | ("movies", "popular"):
                # Unclean Example: Deadpool 2016
                popular_contents = common_func()
                cleaned_contents = second_common_func(popular_contents)
            case ("shows", "anticipated") | ("movies", "anticipated"):
                # Different html tag
                # Unclean Example: Daredevil: Born Again 2025
                anticipated = text_findall_func("a", class_="titles-link")
                cleaned_contents = second_common_func(anticipated)
            case ("movies", "boxoffice"):
                # Example: $36,000,000Dog Man 2025
                boxoffice = common_func()
                pattern = re.compile(r"(\$\d[\d,]*)(\D+)(\d{4})$")
                cleaned_contents = {
                    idx: {
                        "Title": match.group(2).strip(),
                        "Total Budget": match.group(1),
                        "Year": int(match.group(3)),
                    }
                    for idx, i in _enum(boxoffice)
                    if (match := pattern.match(i))
                }

            # ^ -------------------------------------------------------------- ^ #

            # ^ -------------------Match Case for (Calendars)----------------- ^ #
            case ("calendars", "shows"):
                # Example: ' 1:00 amCBS7x11 Welcome to the e-Neighborhood'
                calendar_shows = self._find_all("div", class_="titles has-worded-image")
                pattern = re.compile(r"(\d{1,3}x\d{1,3})\s(\D+)")

                cleaned_contents = {
                    idx: {
                        "Title": (
                            _title_contents := pattern.match(
                                i.find(class_="titles-link").text
                            )
                        ).group(2),
                        "Network": i.find(class_="generic").text,
                        "Season": _title_contents.group(1).split("x")[0],
                        "Episode": _title_contents.group(1).split("x")[1],
                        "Time": i.h4.get_text(strip=True),
                    }
                    for idx, i in _enum(calendar_shows)
                }

                #!> FINISH CALENDARS SECTIONS
            # ^ --------------------------------------------------------- ^ #

            # ^ -------------------Match Case for (People)----------------- ^ #
            case ("people", section):
                common_func = partial(self._find_all, "div")
                person_credits = {
                    idx: i.find(class_="ellipsify").text
                    for idx, i in enumerate_at_one(common_func(class_="titles"))
                }

                person_descr_details = common_func(class_="col-lg-8 col-md-7")
                person_description = next(
                    (i.text.lstrip(i.ul.text) for i in person_descr_details)
                )

                # Example: ['Age60', 'GenderMale', 'Birthday1964-09-02', 'BirthplaceBeirut, Lebanon', 'Known ForActing']
                person_stats = ("Age", "Gender", "Birthday", "Birthplace", "Known For")
                person_details_uncleaned = next(
                    (
                        [j.text for j in i.ul.find_all("li")]
                        for i in person_descr_details
                    )
                )

                cleaned_contents = OrderedDict(
                    {
                        "Person": self._section.lstrip("/").title(),
                        **{
                            j: i.removeprefix(j)
                            for i, j in zip(person_details_uncleaned, person_stats)
                        },
                        "Description": person_description,
                        "Credits": person_credits,
                    }
                )
            # ^ --------------------------------------------------------- ^#

        # ^ No default case needed as all cases are covered and will raise an exception if not found ^ #

        return cleaned_contents

    def get_contents(self):
        return self._clean_contents()


class TraktHub:
    MAIN_DB: str = "https://trakt.tv/"
    CATEGORIES: StrTuple = ("people", "shows", "movies", "calendars")
    SHOW_SECTIONS: StrTuple = ("trending", "popular", "anticipated")
    MOVIE_SECTIONS: StrTuple = (*SHOW_SECTIONS, "boxoffice")
    CALENDARS_SECTIONS: StrTuple = (
        *CATEGORIES[:-1],
        "premieres",
        "new-shows",
        "finales",
        "dvd",
    )
    _ALL_SECTIONS: StrTuple = (*SHOW_SECTIONS, *MOVIE_SECTIONS, *CALENDARS_SECTIONS)

    _APIParser = APIParser

    __slots__ = ("_query", "_category", "_main_url")

    def __init__(
        self,
        *,
        query: Optional[str] = "",
        category: Literal["people", "movies", "shows", "calendars"],
    ):
        self._query, self._category = self._validate_args(query, category)

        self._main_url = self._get_url()

    def _get_url(self):
        main_url = self.MAIN_DB + self._category
        if self._query or self._category == "people":
            main_url += self._query
        return main_url

    def _validate_args(self, *args):
        query, category = args

        if any((map(lambda x: not isinstance(x, str), (query, category)))):
            raise CHException("All arguments must be strings.")

        if category not in (categories := self.CATEGORIES):
            raise CHException(
                f"{category!r} is invalid and must be one of the following:\n{categories}."
            )

        if query or category == "people":
            cleaned_query = query.translate(str.maketrans("", "", punctuation))
            query = "/" + "-".join(cleaned_query.split())

        return query, category

    def _validate_section(self, section: str):
        movie_sections, show_sections, calendars_sections = (
            self.MOVIE_SECTIONS,
            self.SHOW_SECTIONS,
            self.CALENDARS_SECTIONS,
        )

        if section not in self._ALL_SECTIONS:
            raise THException(
                f"{section!r} is not a valid section.\nSection Options:"
                f"\nMovie Sections: {movie_sections}"
                f"\nShow Sections: {show_sections}"
                f"\nCalendar Sections: {calendars_sections}"
            )

        cat = self._category

        def __raise_exception(main_sections):
            _all_sections = {
                "movies": movie_sections,
                "shows": show_sections,
                "calendars": calendars_sections,
            }
            correct_cat = next((k for k, v in _all_sections.items() if section in v))
            if section not in main_sections:
                raise THException(
                    f"{section!r} is not a valid section for category {cat!r}."
                    f"\nThis section is for category {correct_cat!r}."
                )

        # Check if section is in the correct category
        match cat:
            case "movies":
                __raise_exception(movie_sections)
            case "shows":
                __raise_exception(show_sections)
            case "calendars":
                __raise_exception(calendars_sections)

        return section

    @TraktHubViewer._th_viewer()
    def track_hub(
        self,
        section: LiteralSection,
    ):
        valid_section = self._validate_section(section)
        return self._APIParser(self._main_url, valid_section)

    @TraktHubViewer._th_viewer()
    def track_person(self):
        return self._APIParser(self._main_url)

    def search(self):
        parser = self._APIParser(self._main_url)
        parsed_contents = parser.parse_html_contents(parser.contents)

        def _removefix(_string, obj, *, post: bool = True):
            return getattr(_string, "removesuffix" if post else "removeprefix")(obj)

        flix_title_contents = parsed_contents.find(
            "div",
            class_="col-md-10 col-md-offset-2 col-sm-9 col-sm-offset-3 mobile-title",
        ).h1.get_text(separator="#")
        flix_title, release_year, flix_mature_rating = map(
            str.strip, flix_title_contents.split("#")
        )

        loved_percentage, num_of_votes = (
            parsed_contents.find("div", class_=i).text for i in ("rating", "votes")
        )

        uncleaned_stats = next(
            (
                [
                    i.get_text(separator="#", strip=True).split("#")
                    for i in i.find_all("div", class_="number")
                ]
                for i in parsed_contents.find_all("ul", class_="stats")
            )
        )
        space_join = lambda s: " ".join(s)
        imdb_rating, imdb_num_reviews = uncleaned_stats[0]
        tmdb_rating, tmdb_num_reviews = uncleaned_stats[1]
        rotten_rating = space_join(uncleaned_stats[2])

        (
            audience_percent,
            metacritic_rating,
            num_watchers,
            num_plays,
            num_collected,
            num_comments,
            num_lists,
            num_favorited,
        ) = map(itemgetter(0), uncleaned_stats[3:])

        uncleaned_metadata = parsed_contents.find("div", class_="col-lg-8 col-md-7")
        release_date = next((i.span.text for i in uncleaned_metadata if i.span))
        _years_ago = get_datetime().year - int(release_date[:4])
        years_ago = "{ya} year{s} ago".format(
            ya=_years_ago, s="s" if _years_ago != 1 else ""
        )

        # Runtime
        runtime_in_hours = next(
            (
                _i.text
                for i in uncleaned_metadata
                if (_i := i.find("span", class_="humanized-minutes"))
            )
        )
        _time_match = re.match(r"(?:(\d+)h)?\s*(?:(\d+)m)?", runtime_in_hours)
        if _time_match:
            hours = int(_time_match.group(1) or 0)
            minutes = int(_time_match.group(2) or 0)

        runtime_in_minutes = f"{(hours * 60) + minutes}m"

        directors = next(
            (
                list(
                    set(i.meta["content"] for i in i.find_all("span", class_="hidden"))
                )
                for i in uncleaned_metadata
                if i.find("span", class_="hidden")
            )
        )
        director = directors[0]
        writers = next(
            (
                [i.meta["content"] for i in i.find_all(itemprop="writer")]
                for i in uncleaned_metadata
                if i.find("span", class_="hidden", itemprop="writer")
            )
        )

        country = next(
            (
                _removefix(i.text, "Country", post=False)
                for i in uncleaned_metadata.find_all("li", itemprop="countryOfOrigin")
            )
        )

        _languages = next(
            (
                [
                    _removefix(i.text, "Languages", post=False)
                    for i in i.find_all("li")
                    if "Languages" in str(i)
                ]
                for i in uncleaned_metadata
                if i.find("li", itemprop="countryOfOrigin")
            )
        )[0].split(",")
        languages = _languages[0] if len(_languages) == 1 else tuple(_languages)

        _studios = next(
            (
                [
                    _removefix(i.text, "Studios", post=False)
                    for i in i.find_all("li")
                    if "Studios" in str(i)
                ]
                for i in uncleaned_metadata
                if i.find("li", itemprop="countryOfOrigin")
            )
        )
        studios = [
            i[: i.find("+") - 1].strip() if "+" in i else i.strip()
            for i in "".join(_studios).split(",")
        ]
        genres = [i.text for i in uncleaned_metadata.find_all("span", itemprop="genre")]
        spoiler, description = next(
            (
                [
                    i.find("div", id="tagline").text,
                    i.find("div", class_="readmore").text,
                ]
                for i in uncleaned_metadata.find_all(
                    "div", {"data-spoiler-movie-id": True}
                )
            )
        )
        _actors_table = [
            [i.find(class_=j).text for j in ("name", "character")]
            for i in parsed_contents.find_all("li", itemprop="actor")
        ]
        actors_table = tuple(i + f" [{j}]" for i, j in _actors_table)

        organized_data = OrderedDict(
            {
                "Basic Info": OrderedDict(
                    {
                        "Title": flix_title,
                        "Release Year": release_year,
                        "Content Rating": flix_mature_rating,
                    }
                ),
                "Ratings": OrderedDict(
                    {
                        "Loved %": (loved_percentage, num_of_votes),
                        "IMDb": (imdb_rating, imdb_num_reviews),
                        "TMDb": (tmdb_rating, tmdb_num_reviews),
                        "Rotten Tomatoe": rotten_rating,
                        "Metacritic": metacritic_rating,
                        "Audience %": audience_percent,
                    }
                ),
                "Total Engagement": OrderedDict(
                    {
                        "Watchers": num_watchers,
                        "Plays": num_plays,
                        "Collected": num_collected,
                        "Comments": num_comments,
                        "Personal Lists": num_lists,
                        "Favorited": num_favorited,
                    }
                ),
                "Release Details": OrderedDict(
                    {
                        "Release Date": (release_date, years_ago),
                        "Runtime": (runtime_in_hours, runtime_in_minutes),
                    }
                ),
                "Production": OrderedDict(
                    {
                        "Country": country,
                        "Languages": languages,
                        "Studios": studios,
                        "Genres": genres,
                        "Director": director,
                        "Directors": directors,
                        "Writers": writers,
                    }
                ),
                "Narrative": OrderedDict(
                    {
                        "Spoiler": spoiler,
                        "Description": description,
                    }
                ),
                "Cast": OrderedDict(
                    {
                        "Actors": actors_table,
                    }
                ),
            }
        )

        return organized_data


# from pprint import pprint as print

# th = TraktHub(category="shows")
# trending = th.track_hub("trending")
# print(trending)

# th = TraktHub(category="shows")
# popular = th.track_hub("popular")
# print(popular)

# th = TraktHub(category="shows")
# anticipated = th.track_hub("anticipated")
# print(anticipated)

# bo = TraktHub(category="movies")  # boxoffice only for movies
# boxoffice = bo.track_hub("boxoffice")
# print(boxoffice)

# Calendars
# ca = TraktHub(category="calendars")
# ca_contents = ca.track_hub("shows")
# print(ca_contents)


# # People
# people = TraktHub(query="Keanu Reeves", category="people")
# print(people.track_person())
# people = TraktHub(query="the matrix 1999", category="movies")
# print(people.search())
# people = TraktHub(query="moana 2 2024", category="movies")
# print(people.search())
# people = TraktHub(query="Apocalypse Now 1979", category="movies")
# print(people.search())


__all__ = (
    "TraktHub",
    "TraktHubViewer",
)
