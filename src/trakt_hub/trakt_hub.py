import re
import sys
from collections import OrderedDict
from functools import partial, wraps
from operator import itemgetter
from string import punctuation
from time import sleep

from .trakt_utils.parsers import APIParser
from .trakt_utils.type_hints import (
    IntOrStr,
    Literal,
    LiteralCategory,
    LiteralSection,
    Optional,
    StrTuple,
)
from .trakt_utils.exceptions import THException
from .trakt_utils.utils import (
    BeautifulSoup,
    enumerate_at_one,
    get_datetime,
    get_terminal_size,
    removefix,
)


class TraktHubViewer:
    """
    A class to view the contents of the Trakt.tv.
    
    #### Attributes:
        - `category`: The category to view.
        - `section`: The section to view.
        - `html_contents`: The HTML contents of the page.
    
    #### Methods:
        - `get_contents`: Get the cleaned contents.
        - `print_contents`: Print the cleaned contents.
    
    #### Raises:
        - `THException`: If any of the arguments are invalid
            or if the section is not valid for the category.
    
    #### Notes:
        - The `category` attribute must be a valid category.
        - The `section` attribute must be a valid section for the category.
    """
    
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

        def second_common_func(contents):
            pattern = re.compile(r"(\w+)(.*?)\s(\d{4})$")
            return {
                idx: {
                    "Title": match.group(1) + match.group(2),
                    "Year": int(match.group(3)),
                }
                for idx, i in enumerate_at_one(contents)
                if (match := pattern.match(i))
            }

        cleaned_contents = None

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
                    for idx, i in enumerate_at_one(trending)
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
                    for idx, i in enumerate_at_one(boxoffice)
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
                        **{
                            k: _title_contents.group(1).split("x")[v]
                            for k, v in (("Season", 0), ("Episode", 1))
                        },
                        "Time": i.h4.get_text(strip=True),
                    }
                    for idx, i in enumerate_at_one(calendar_shows)
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

    @staticmethod
    def print_contents(contents):
        if isinstance(contents, (bool, str)):
            # For cases for all:
            #   ~ '--<arg>' commands (Returned obj is type str)
            #   ~ Is-Functions (Returned obj is type boolean)
            print(contents)
            sys.exit()

        cli_args = sys.argv
        verbose = False

        if "--verbose" in cli_args:
            cli_args.remove("--verbose")
            verbose = True

        function_name = query = cli_args[1]
        terminal_col, _terminal_lines = get_terminal_size()

        def print_header(*args):
            current_dt = get_datetime(with_time=True)
            sep = "-" * (terminal_col // 2)
            header = "TraktHub - {} {}"
            print(sep, end="\n\n")
            header = header.format(
                *args,
            ).center(((terminal_col + len(header)) // 2) - len("TraktHub"), "-")
            print(header, end="\n\n")
            print(sep)
            print(f"Time Now: {current_dt}", end="\n\n")

        def verbose_output(code: int, c=""):
            match code:
                case 1:
                    print(
                        "~ Trakt.tv has been successfully accessed and the data has been retrieved."
                    )
                    print("~ Formatting the data for display...")
                    sleep(0.5)
                case 2:
                    print(f"~ Creating a formatted display for '{c}'.")
                    print("~ This may take a few seconds...")
                    sleep(2)
                    print("~ The formatted data will now be displayed.", end="\n\n")
                    sleep(1)

        value_string = partial("{:>5}• {k}{:>5}: {v}".format, " ", " ")
        
        if verbose:
            verbose_output(1)

        if function_name.startswith("get"):
            # All Get-Functions (Returned obj is type dict)

            # 'get-trending' -> 'trending'
            f_name = function_name.split("-")[-1]
            if function_name.endswith("boxoffice"):
                f_name = "Current"
                cat = "boxoffice"
            else:
                # 'movies' or 'shows'
                cat = cli_args[2][3:]

            if verbose:
                verbose_output(2)

            print_header(*(i.title() for i in (f_name, cat)))

            # popular and anticipated only have title and year
            common_keys = ("Title", "Year")
            diff_set = lambda x: len(set(x) - set(common_keys))
            for idx, v in contents.items():
                match diff_set(v):
                    case 0:
                        # Get-Popular/Anticipated functions
                        print(f"{idx}: {v['Title']} ({v['Year']})")
                    case 1:
                        # Boxoffice
                        def _format(*args):
                            print(
                                f"{idx}-{v['Title']} ({v['Year']})",
                                "\n{:>5}• {}: {}".format(" ", *args),
                            )

                        uncommon_keys = ("Total Budget", "Watch Count")

                        if cat == "boxoffice":
                            _format(uncommon_keys[0], v[uncommon_keys[0]])
                        elif cat in ("movies", "shows"):
                            _format(uncommon_keys[1], v[uncommon_keys[1]])
        elif query in ("-q", "--query"):
            cat = cli_args[-1]
            
            if verbose:
                verbose_output(2, cat)
            
            if cat == "movies":
                header_title = (
                    contents["Basic Info"][i] for i in ("Title", "Release Year")
                )
                print_header(*header_title)

                for header_section, header_values in contents.items():
                    print(f"\n\n[{header_section}]")
                    for key, value in header_values.items():
                        if isinstance(value, (list, tuple)):
                            if header_section == "Cast":
                                p = re.compile(r"^(.*?)\s*\[((.*?))\]$")
                                actors = tuple(
                                    (m.group(1), f"as {m.group(2)}")
                                    for av in value
                                    if (m := p.match(av))
                                )
                                for actors_name, role_name in actors:
                                    print(value_string(k=actors_name, v=role_name))
                            else:
                                value = ", ".join(map(str, value))
                                print(value_string(k=key, v=value))
                        else:
                            print(value_string(k=key, v=value))
            elif cat == "people":
                person = contents["Person"]
                keyval_sep = "-" * 6

                print_header(person, "")

                for key, value in contents.items():
                    if key == "Credits":
                        print(f"• {key}:")
                        for idx, credit in value.items():
                            print(f"{'':2}{idx}:{keyval_sep} {credit}")
                    else:
                        if key == "Description":
                            value = "\n" + value + "\n"
                            keyval_sep = ""
                        print(f"• {key}:{keyval_sep} {value}")
            elif cat == "shows":
                show_title = contents["Basic Info"]["Title"]
                print_header(show_title, "")
                
                for header_section, header_values in contents.items():
                    print(f"[{header_section}]")
                    for section, values in header_values.items():
                        if isinstance(values, tuple):
                            values = ", ".join(values)
                        print(value_string(k=section, v=values))


class TraktHub:
    """
    A class for interacting with the `Trakt.tv` database by categorizing and retrieving
    information on movies, TV shows, people, and calendar events.

    ### Attributes:
    `MAIN_DB` : str
        The base URL for Trakt.tv (`https://trakt.tv/`), used as the primary database.

    `CATEGORIES` : Tuple[str, ...]
        A tuple representing the main content categories available on Trakt:
        - people           : Queries related to actors, directors, and crew members.
        - shows            : Queries related to TV shows.
        - movies           : Queries related to movies.
        - calendars        : Queries related to release calendars.

    `SHOW_SECTIONS` : Tuple[str, ...]
        Sections specific to TV shows:
        - trending         : Lists currently trending TV shows.
        - popular          : Lists popular TV shows based on user ratings and activity.
        - anticipated      : Lists most anticipated TV shows.

    `MOVIE_SECTIONS` : Tuple[str, ...]
        Sections specific to movies, including those from `_SHOW_SECTIONS`:
        - trending         : Lists currently trending movies.
        - popular          : Lists popular movies based on user ratings and activity.
        - anticipated      : Lists most anticipated movies.
        - boxoffice        : Lists movies currently performing well at the box office.

    `CALENDARS_SECTIONS` : Tuple[str, ...]
        Sections specific to Trakt's calendar feature, which organizes upcoming releases:
        - people           : Calendar section related to people (e.g., actor appearances).
        - shows            : Calendar section related to TV shows.
        - movies           : Calendar section related to movies.
        - premieres        : Lists upcoming movie/show premieres.
        - new-shows        : Lists newly released TV shows.
        - finales          : Lists upcoming season/series finales.
        - dvd              : Lists upcoming DVD/Blu-ray releases.

    `ALL_SECTIONS` : Tuple[str, ...]
        A combined tuple of all available sections across shows, movies, and calendars.

    ### Parameters:
        search : str, optional
            The search term used to query movies, TV shows, or people. Default is an empty string.

        category : Literal["people", "movie", "show", "calendar"], optional
            The category of content to search within. Must be one of:
            - "people"   : Searches for actors, directors, or crew members.
            - "movie"    : Searches for movies.
            - "show"     : Searches for TV shows.
            - "calendar" : Searches within the calendar feature.

        section : Optional[Literal["trending", "popular", "anticipated", "boxoffice", "premieres", "new-shows", "finales", "dvd"]], optional
            A subsection within the selected category to refine search results. Default is an empty string.

        year : Optional[IntOrStr], optional
            An optional argument to specify a year filter for movies or TV shows.
            If an error occurs during querying, a valid `year` argument may be required.
    
    
    #### Methods:
        - `track_hub`: Track the hub for the provided section.
        - `track_person`: Track the person for the provided query.
        - `search`: Search for the provided query.
    
    #### Raises:
        - `THException`: If any of the arguments are invalid
            or if the section is not valid for the category.
    """
    
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

    __slots__ = ("_query", "_category", "_main_url", "_page_number")

    def __init__(
        self,
        *,
        query: Optional[str] = "",
        category: Literal["people", "movies", "shows", "calendars"],
        **kwargs,
    ):
        self._query, self._category, self._page_number = self._validate_args(
            query, category, **kwargs
        )
        self._main_url = self._get_url()

    def _get_url(self):
        main_url = self.MAIN_DB + self._category
        if self._query or self._category == "people":
            main_url += self._query
        return main_url

    def _validate_args(self, *args, **kwargs):
        query, category = args
        page_number = kwargs.get("page_number", "")

        if any((map(lambda x: not isinstance(x, str), (query, category)))):
            raise THException("All arguments must be strings.")

        if not isinstance(page_number, IntOrStr):
            raise THException(
                f"Page number must be an integer or a string, not {type(page_number).__name__}."
            )

        if category not in (categories := self.CATEGORIES):
            raise THException(
                f"{category!r} is invalid and must be one of the following:\n{categories}."
            )

        if query or category == "people":
            cleaned_query = query.translate(str.maketrans("", "", punctuation))
            query = "/" + "-".join(cleaned_query.split())

        return query, category, page_number

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

        if pg := self._page_number:
            section += f"?page={pg}"

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

    def _search_show(self, __contents):
        show_title = self._main_url.split("/")[-1].split("-")[0].title()
        show_stats = __contents.find_all(
            "div",
            class_="col-md-10 col-md-offset-2 col-sm-9 col-sm-offset-3 ul-wrapper",
        )

        def str_translate(str_obj):
            return str_obj.translate(str.maketrans("#", " ")).strip()

        rating_stats_unclean = next(
            [
                i.get_text(strip=True, separator="#")
                for i in i.find_all("div", class_="number")
            ]
            for i in show_stats
        )
        rating_stats_unclean.pop(1)
        (
            loved_votes,
            imdb_stats,
            tmdb_stats,
            fresh_value,
            audience,
            streaming_rank,
            watchers_count,
            num_of_plays,
            collected_count,
            num_of_comments,
            num_of_lists,
            num_favorited,
        ) = rating_stats_unclean

        loved_perc, loved_votes = str_translate(removefix(loved_votes, "votes")).split()
        imdb_score, imdb_nums = imdb_stats.split("#")
        tmdb_score, tmdb_nums = tmdb_stats.split("#")
        fresh_value = str_translate(fresh_value)
        audience = str_translate(removefix(audience, "Audience"))
        justwatch_score, *justwatch_trend = str_translate(streaming_rank).split()
        justwatch_trend = " ".join(justwatch_trend)
        (
            watchers_count,
            num_of_plays,
            collected_count,
            num_of_comments,
            num_of_lists,
            num_favorited,
        ) = [
            str_translate(removefix(*i))
            for i in (
                (watchers_count, "watchers"),
                (num_of_plays, "plays"),
                (collected_count, "collected"),
                (num_of_comments, "comments"),
                (num_of_lists, "lists"),
                (num_favorited, "favorited"),
            )
        ]

        show_details = __contents.find_all("div", class_="col-lg-8 col-md-7")
        spoiler = next((i.find("div", id="tagline").text for i in show_details))
        description = next(
            (i.find("div", class_="readmore").text for i in show_details)
        )
        num_of_seasons = next(
            (
                i.find("a", class_="season-count").text
                for i in __contents.find_all(
                    "div", class_="col-md-2 col-sm-3 hidden-xs sticky-wrapper"
                )
            )
        )

        organized_data = OrderedDict(
            {
                "Basic Info": OrderedDict(
                    {
                        "Title": show_title,
                        "Total Seasons": num_of_seasons,
                    }
                ),
                "Ratings": OrderedDict(
                    {
                        "Loved %": (loved_perc, loved_votes),
                        "IMDb": (imdb_score, imdb_nums),
                        "TMDb": (tmdb_score, tmdb_nums),
                        "Rotten Tomatoe": fresh_value,
                        "JustWatch": (justwatch_score, justwatch_trend),
                        "Audience %": audience,
                    }
                ),
                "Total Engagement": OrderedDict(
                    {
                        "Watchers": watchers_count,
                        "Plays": num_of_plays,
                        "Collected": collected_count,
                        "Comments": num_of_comments,
                        "Personal Lists": num_of_lists,
                        "Favorited": num_favorited,
                    }
                ),
                "Narrative": OrderedDict(
                    {
                        "Spoiler": spoiler,
                        "Description": description,
                    }
                ),
            }
        )

        return organized_data

    def search(self):
        parser = self._APIParser(self._main_url)
        parsed_contents = parser.parse_html_contents(parser.contents)
        if self._category == "shows":
            return self._search_show(parsed_contents)

        flix_title_contents = parsed_contents.find(
            "div",
            class_="col-md-10 col-md-offset-2 col-sm-9 col-sm-offset-3 mobile-title",
        ).h1.get_text(separator="#")

        try:
            flix_title, release_year, flix_mature_rating = map(
                str.strip, flix_title_contents.split("#")
            )
        except ValueError:
            raise THException(
                "Unable to parse the contents for the provided query."
                "\nSome contents may be missing on URL the page."
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
                removefix(i.text, "Country", post=False)
                for i in uncleaned_metadata.find_all("li", itemprop="countryOfOrigin")
            )
        )

        _languages = next(
            (
                [
                    removefix(i.text, "Languages", post=False)
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
                    removefix(i.text, "Studios", post=False)
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


__all__ = (
    "TraktHub",
    "TraktHubViewer",
)
