import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from turbopaster.exceptions import ApplicationError
from turbopaster.snippets import load_user_snippets


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Search and insert saved text snippets.")
    parser.add_argument(
        "--app-dir",
        type=Path,
        metavar="PATH",
        help="use PATH for config.yaml and the snippets/ folder",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="open an interactive search window",
    )
    args = parser.parse_args(argv)

    try:
        mappings = load_user_snippets(args.app_dir)
    except ApplicationError as exc:
        print(f"turbopaster: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if args.search:
        from turbopaster.search import run_search_window

        selected = run_search_window(mappings)
        if selected is not None:
            print(selected)
        return

    print(f"loaded {len(mappings)} snippets")
    for key in mappings:
        print(f"  {key}")


if __name__ == "__main__":
    main()
