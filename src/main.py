import argparse
from pathlib import Path
from src.parser import Parser


def main():
    parser = argparse.ArgumentParser(
        description="Runbook Config Processor"
    )
    parser.add_argument(
        '-f',
        '--file',
        required=True,
        help='Path to YAML config file'
    )
    args = parser.parse_args()

    # Process config file
    config = Parser.parse_config(Path(args.file))
    print(
        "Successfully parsed config: Version "
        f"{config.version}, {len(config.runbooks)} runbooks found"
    )


if __name__ == "__main__":
    main()
