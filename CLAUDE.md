# CLAUDE.md

Guidelines and decisions for working on this repository.

## Project Overview

kiwix-host is a Docker Compose wrapper around `kiwix-serve` that serves ZIM archives locally for offline access. ZIM files live in `./data/` and are never committed to git.

Two components:
- **kiwix-serve** (`docker-compose.yml`) — serves ZIM files over HTTP
- **downloader** (`download.py` + `Dockerfile`) — downloads Stack Exchange sites as ZIM files using sotoki

## Architecture Decisions

### ZIM files go in `./data/`, never git
`/data/*.zim` is gitignored. The `./data/` directory is tracked via `.gitkeep` only.

### Downloader wraps sotoki via subprocess
`download.py` calls the `sotoki` CLI through `subprocess.run` rather than importing sotoki's Python API. This keeps the script thin and insulates it from sotoki internal API changes.

### Output directory is resolved relative to `__file__`
`OUTPUT_DIR = Path(__file__).parent / "data"` so the script works correctly regardless of the working directory the user invokes it from.

### sotoki always receives `--output`
sotoki has no default output directory. Always pass `--output` explicitly.

### Optional flags are only forwarded when explicitly set
`--threads`, `--without-images`, and `--debug` default to `None`/`False` and are only appended to the sotoki command when the user passes them. This lets sotoki's own defaults apply rather than duplicating them.

### Dockerfile uses `python:3.12-slim`
Keeps the image small. The container mounts `./data` to `/app/data` at runtime — it is not baked into the image.

### Docker run mounts `./data` to `/app/data`
```bash
docker run --rm -v ./data:/app/data kiwix-downloader ...
```
This aligns with `OUTPUT_DIR` inside the container (`/app/data` = `Path(__file__).parent / "data"`).

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
