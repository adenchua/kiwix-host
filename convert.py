#!/usr/bin/env python3
"""Convert a local Stack Exchange 7z dump into a ZIM file in ./data/."""

import argparse
import functools
import socket
import subprocess
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data"
WRAPPER_PATH = Path(__file__).parent / "sotoki_wrapper.py"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a local Stack Exchange 7z dump into a ZIM file in ./data/",
    )
    parser.add_argument(
        "--dump",
        required=True,
        help="Path to local 7z dump file, e.g. ./input/stackoverflow.com.7z",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help='Stack Exchange domain (inferred from filename if omitted, e.g. "stackoverflow.com")',
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

    dump_path = Path(args.dump).resolve()
    if not dump_path.is_file():
        sys.exit(f"Error: dump file not found: {dump_path}")

    domain = args.domain or dump_path.stem
    if dump_path.name != f"{domain}.7z":
        sys.exit(
            f"Error: filename '{dump_path.name}' does not match domain '{domain}'. "
            f"sotoki will request '{domain}.7z' from the mirror. "
            f"Rename the file or pass --domain explicitly."
        )

    # Bind to a free port before starting the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    handler = functools.partial(_QuietHandler, directory=str(dump_path.parent))
    server = HTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(WRAPPER_PATH),
        "--domain", domain,
        "--mirror", f"http://127.0.0.1:{port}",
        "--title", args.title,
        "--description", args.description,
        "--output", str(OUTPUT_DIR),
        "--redis-url", "redis://localhost:6379",
    ]
    if args.threads is not None:
        cmd += ["--threads", str(args.threads)]
    if args.without_images:
        cmd.append("--without-images")
    if args.debug:
        cmd.append("--debug")

    print(f"Serving {dump_path.name} from http://127.0.0.1:{port}")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    server.shutdown()
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
