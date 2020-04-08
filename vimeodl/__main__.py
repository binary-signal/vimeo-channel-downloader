import sys
import argparse

from vimeodl import log
from vimeodl.vimeo import VimeoDownloader, VimeoLinkExtractor


def check_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", metavar="url", type=str, help="Vimeo url to download")

    parser.add_argument(
        "-o",
        "--output",
        help="directory like object to save  extracted videos",
        default="vimeos",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--resume",
        action="store_true",
        help="If a download session has failed set this flag to resume download",
        default="store_false",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = check_arg()
    if not args.url.endswith("/videos") or "vimeo.com/" not in args.url:
        log.error(
            "Error: Invalid vimeo url expected something like `https://vimeo.com/vjloop/videos`"
        )
        sys.exit(-1)

    vim = VimeoDownloader(args.url, args.output, args.resume)
    vim.download()
