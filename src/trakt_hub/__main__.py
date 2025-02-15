from .trakt_hub import TraktHubViewer
from .trakt_utils.cli import cli_parser


if __name__ == "__main__":
    TraktHubViewer.print_contents(cli_parser())