from argparse import ArgumentParser

from .parsers import _metadata_parser
from ..trakt_hub import TraktHubViewer
from ..trakt_functions.functions import (
    get_anticipated,
    get_boxoffice,
    get_popular,
    get_trending,
    is_anticipated,
    is_popular,
    is_trending,
    trakt_query,
)


def cli_parser():
    arg_parser = ArgumentParser(
        description="A CLI for parsing and viewing Trakt-TV data."
    )
    sub_parsers = arg_parser.add_subparsers(dest="command", help="All CLI options.")

    def _add_args(parser):
        def wrapper(*args, **kwargs):
            if all(("action" not in kwargs, all(s.startswith("--") for s in args))):
                kwargs["action"] = "store_true"
            else:
                kwargs["type"] = str
            return parser.add_argument(*args, **kwargs)

        return wrapper

    # TraktHub-Arguments
    _add_args(arg_parser)("-q", "--query")
    _add_args(arg_parser)("-c", "--category")

    # Main-Commands
    main_args = _add_args(arg_parser)
    main_args("--version", help="Display the current version of 'trakt_hub'.")
    main_args("--author", help="Display the author of 'trakt_hub'.")
    main_args("--license", help="Display the license of 'trakt_hub'.")
    main_args("--description", help="Display the description of 'trakt_hub'.")
    main_args("--url", help="Display the GitHub URL of 'trakt_hub'.")
    main_args("--verbose", help="Enable verbose output.")

    # Get-Boxoffice
    boxoffice = sub_parsers.add_parser(
        "get-boxoffice",
        argument_default="movies",
        description="Get the budget of current box office movies.",
    )

    # Get-Trending
    trending = sub_parsers.add_parser("get-trending", description="Get trending data.")
    trending_args = _add_args(trending)
    trending_args("--tshows", help="Get current trending shows.")
    trending_args("--tmovies", help="Get current trending movies.")

    # Get-Popular
    popular = sub_parsers.add_parser("get-popular", description="Get popular data.")
    popular_args = _add_args(popular)
    popular_args("--pshows", help="Get current popular shows.")
    popular_args("--pmovies", help="Get current popular movies.")

    # Get-Anticipated
    anticipated = sub_parsers.add_parser(
        "get-anticipated", description="Get anticipated data."
    )
    anticipated_args = _add_args(anticipated)
    anticipated_args("--ashows", help="Get current anticipated shows.")
    anticipated_args("--amovies", help="Get current anticipated movies.")

    # Is-Trending
    istrending = sub_parsers.add_parser(
        "is-trending", description="Check if a show or movie is trending."
    )
    istrending_args = _add_args(istrending)
    istrending_args("-q", "--query", help="Movie or show to check if it is trending.")
    istrending_args(
        "-c", "--category", help="Specify the category of the show or movie."
    )

    # Is-Anticipated
    isanticipated = sub_parsers.add_parser(
        "is-anticipated", description="Check if a show or movie is anticipated."
    )
    isanticipated_args = _add_args(isanticipated)
    isanticipated_args(
        "-q", "--query", help="Movie or show to check if it is trending."
    )
    isanticipated_args(
        "-c", "--category", help="Specify the category of the show or movie."
    )

    # Is-Popular
    ispopular = sub_parsers.add_parser(
        "is-popular", description="Check if a show or movie is popular."
    )
    ispopular_args = _add_args(ispopular)
    ispopular_args("-q", "--query", help="Movie or show to check if it is popular.")
    ispopular_args(
        "-c", "--category", help="Specify the category of the show or movie."
    )

    metadata = _metadata_parser()

    args = arg_parser.parse_args()

    def mult_args(func):
        q, c = map(
            lambda x: getattr(args, x[x[-1] in args.__dict__]),
            (["q", "query"], ["c", "category"]),
        )
        return func(query=q, category=c)

    # Main-Arguments
    if args.version:
        return metadata["version"]
    elif args.author:
        return metadata["author"]
    elif args.license:
        return metadata["license"]
    elif args.description:
        return metadata["description"]
    elif args.url:
        return metadata["url"]

    # 'get_<category>' function Arguments
    elif args.command == "get-boxoffice":
        return get_boxoffice("movies")
    elif args.command == "get-trending":
        if args.tshows:
            return get_trending("shows")
        return get_trending("movies")
    elif args.command == "get-popular":
        if args.pshows:
            return get_popular("shows")
        return get_popular("movies")
    elif args.command == "get-anticipated":
        if args.ashows:
            return get_anticipated("shows")
        return get_anticipated("movies")

    # 'is_<category>' function Arguments
    elif args.command == "is-trending":
        return mult_args(is_trending)
    elif args.command == "is-popular":
        return mult_args(is_popular)
    elif args.command == "is-anticipated":
        return mult_args(is_anticipated)

    # Main Query for TraktHub
    return mult_args(trakt_query)


if __name__ == "__main__":
    TraktHubViewer.print_contents(cli_parser())
