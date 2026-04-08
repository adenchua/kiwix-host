# CLAUDE.md

Guidelines and decisions for working on this repository.

## Project Overview

kiwix-host is a Docker Compose wrapper around `kiwix-serve` that serves ZIM archives locally for offline access. ZIM files live in `./data/` and are never committed to git.

Three components:
- **kiwix-serve** (`docker-compose.yml`) — serves ZIM files over HTTP
- **downloader** (`download.py` + `Dockerfile`) — downloads Stack Exchange sites as ZIM files using sotoki
- **converter** (`convert.py` + `Dockerfile`) — converts a locally pre-downloaded Stack Exchange 7z dump into a ZIM file using sotoki

## Architecture Decisions

### ZIM files go in `./data/`, never git
`/data/*.zim` is gitignored. The `./data/` directory is tracked via `.gitkeep` only.

### Downloader wraps sotoki via subprocess
`download.py` calls sotoki through `subprocess.run` rather than importing sotoki's Python API. This keeps the script thin and insulates it from sotoki internal API changes.

The entry point is `sotoki_wrapper.py`, not the `sotoki` CLI directly. The wrapper patches `requests.Session` and the module-level request functions before delegating to `sotoki.__main__.main()`. There is no sotoki CLI flag to configure HTTP behavior.

The wrapper does three things:

1. **Firefox TLS impersonation via `curl_cffi`** — replaces `requests.Session` with `_FirefoxSession(curl_cffi.requests.Session)`. This produces a real BoringSSL/Firefox TLS handshake, bypassing Cloudflare bot detection that rejects Python's default JA3 fingerprint. A User-Agent header alone is insufficient; Cloudflare checks the TLS fingerprint.

2. **`requests` API compatibility shim (`_CompatResponse`)** — `curl_cffi` returns its own `Headers` and `Response` types that fail `beartype` checks inside `zimscraperlib` (which expects `requests.structures.CaseInsensitiveDict`). `_CompatResponse` wraps every curl_cffi response and converts `headers` to the expected type. It also overrides `raise_for_status` to raise `requests.exceptions.HTTPError` (not `curl_cffi`'s own error type) and logs the URL to stderr when a 4xx occurs.

3. **`Referer` injection + fallback chain** — some CDN-hosted sub-resources (favicons, images) return 403 without a `Referer` header. The wrapper injects `Referer: https://<host>/` on every request unless already set. If curl_cffi raises a transport-level exception (e.g. BoringSSL TLS 1.3 downgrade rejection on non-Cloudflare CDNs like `i.stack.imgur.com`), it falls back to the original `requests.Session`. If curl_cffi gets a 403, the fallback is also attempted before giving up.

### Output directory is resolved relative to `__file__`
`OUTPUT_DIR = Path(__file__).parent / "data"` so the script works correctly regardless of the working directory the user invokes it from.

### sotoki always receives `--output`
sotoki has no default output directory. Always pass `--output` explicitly.

### Optional flags are only forwarded when explicitly set
`--threads`, `--without-images`, and `--debug` default to `None`/`False` and are only appended to the sotoki command when the user passes them. This lets sotoki's own defaults apply rather than duplicating them.

### Dockerfile uses `python:3.14`
Uses the full image (not slim) to ensure system libraries like `libcairo2` (required by `cairocffi`/sotoki) and `g++` (required to compile some transitive dependencies) are available without any manual apt installs. The container mounts `./data` to `/app/data` at runtime — it is not baked into the image.

Python 3.14 is required because `sotoki>=3.0.0` dropped the `cchardet` dependency (which was abandoned and failed to compile on Python 3.11+). Earlier Python versions cannot build `cchardet` from source and there is no maintained compatible release.

### Docker run mounts `./data` to `/app/data`
```bash
docker run --rm -v ./data:/app/data kiwix-downloader ...
```
This aligns with `OUTPUT_DIR` inside the container (`/app/data` = `Path(__file__).parent / "data"`).

### Local dump conversion uses a temporary localhost HTTP server
`convert.py` feeds a local 7z dump to sotoki without modifying sotoki internals. sotoki always fetches its dump via `{mirror}/{domain}.7z` — there is no `--local-dump` flag. `convert.py` works around this by starting a `http.server.HTTPServer` (stdlib) on a free port serving the dump's parent directory, then passing `http://127.0.0.1:{port}` as `--mirror`. The server runs in a `daemon=True` thread and is shut down after sotoki exits.

The dump filename must be `{domain}.7z` (e.g. `stackoverflow.com.7z`) because sotoki constructs the download URL as `{mirror}/{domain}.7z`. This is validated early with a clear error message.

For Docker, the input directory must be mounted: `-v ./input:/app/input`.

### `entrypoint.sh` dispatches on the first argument
When the first argument is `convert`, the entrypoint shifts it off and runs `convert.py`. Otherwise it runs `download.py`. Redis is started unconditionally since sotoki requires it regardless of source mode.

### Downloader Dockerfile is separate from docker-compose.yml
`docker-compose.yml` uses a prebuilt image (`ghcr.io/kiwix/kiwix-serve:latest`) and has no `build:` key. The `Dockerfile` is solely for the downloader and must be built manually before use.

## Stack Exchange Mirror

Default mirror: `https://archive.org/download/stackexchange`

For reproducible builds, override with a dated snapshot:
```bash
--mirror https://archive.org/download/stackexchange_20240829
```

## Adding a New Downloader Source

Currently only Stack Exchange (via sotoki) is supported. If adding support for other ZIM sources (e.g., direct HTTP downloads from download.kiwix.org), add a separate subcommand or script rather than overloading `download.py`.

## Python Style

- No classes — flat functions only
- `argparse` for CLI argument parsing
- Stream subprocess output directly to terminal (no `capture_output`)
- Propagate subprocess exit codes via `sys.exit(result.returncode)`
