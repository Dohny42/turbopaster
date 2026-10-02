import sys
from pathlib import Path

from turbopaster.snippets import SnippetError, load_directory


def main() -> None:
    directory = Path("snippets")
    try:
        mappings = load_directory(directory)
    except SnippetError as exc:
        print(f"turbopaster: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    print(f"loaded {len(mappings)} snippets")
    for key in mappings:
        print(f"  {key}")


if __name__ == "__main__":
    main()
