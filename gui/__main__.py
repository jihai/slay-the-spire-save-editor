"""Allow running the GUI with: python -m gui [--game 1|2]"""

import argparse
import sys

from gui.app import main


def cli() -> None:
    parser = argparse.ArgumentParser(description="Slay the Spire Save Editor")
    parser.add_argument(
        "--game",
        type=int,
        choices=[1, 2],
        default=1,
        help="Game version: 1 for STS1 (default), 2 for STS2",
    )
    args = parser.parse_args()
    main(game_version=args.game)


cli()
