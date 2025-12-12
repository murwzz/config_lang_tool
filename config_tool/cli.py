import argparse
import json
import sys

from .errors import ConfigToolError
from .parser import parse_config


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="config-tool",
        description="Учебный конфигурационный язык -> JSON",
    )
    parser.add_argument("--input", "-i", required=True, help="Путь к входному файлу")
    parser.add_argument("--pretty", action="store_true", help="Печатать JSON с отступами")

    args = parser.parse_args(argv)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

        data = parse_config(text)

        if args.pretty:
            out = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            out = json.dumps(data, ensure_ascii=False)

        print(out)
        return 0

    except FileNotFoundError:
        print(f"Файл не найден: {args.input}", file=sys.stderr)
        return 2
    except ConfigToolError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
