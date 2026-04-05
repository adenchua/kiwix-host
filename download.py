#!/usr/bin/env python3
"""Download a Stack Exchange site as a ZIM file into ./data/."""

import argparse
import subprocess
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data"

DEFAULT_MIRROR = "https://archive.org/download/stackexchange"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download a Stack Exchange site as a ZIM file into ./data/",
    )
    parser.add_argument(
        "--domain",
        required=True,
        help='Stack Exchange site domain, e.g. "stackoverflow.com"',
    )
    parser.add_argument(
        "--title",
        required=True,
        help="ZIM title (max 30 characters)",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="ZIM description (max 80 characters)",
    )
    parser.add_argument(
        "--mirror",
        default=DEFAULT_MIRROR,
        help=f"Mirror URL for Stack Exchange XML dumps (default: {DEFAULT_MIRROR})",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of worker threads (sotoki default: 1)",
    )
    parser.add_argument(
        "--without-images",
        action="store_true",
        help="Exclude images to reduce ZIM size",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug output from sotoki",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "sotoki",
        "--domain", args.domain,
        "--mirror", args.mirror,
        "--title", args.title,
        "--description", args.description,
        "--output", str(OUTPUT_DIR),
    ]
    if args.threads is not None:
        cmd += ["--threads", str(args.threads)]
    if args.without_images:
        cmd.append("--without-images")
    if args.debug:
        cmd.append("--debug")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
