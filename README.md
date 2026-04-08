# kiwix-host

Hosts [Kiwix](https://www.kiwix.org) ZIM archives locally for offline access using [kiwix-serve](https://github.com/kiwix/kiwix-tools).

## Usage

1. Drop ZIM files into `./data/` (download them from [download.kiwix.org](https://download.kiwix.org/zim/)) or the [librar](https://library.kiwix.org/)
2. Copy `.env.example` to `.env` and adjust `PORT` if needed
3. Start the server:

```bash
docker compose up -d
```

4. Open `http://localhost:8080` in your browser

## Configuration

| Variable | Default | Description                        |
| -------- | ------- | ---------------------------------- |
| `PORT`   | `8080`  | Host port to expose kiwix-serve on |

## Downloading ZIM Files

To download Stack Exchange sites as ZIM files directly into `./data/`, use the included `download.py` script powered by [sotoki](https://github.com/openzim/sotoki).

**Option A — Docker (no Python required):**

```bash
docker build -t kiwix-downloader .
docker run --rm -v ./data:/app/data kiwix-downloader \
  --domain stackoverflow.com \
  --title "Stack Overflow" \
  --description "Q&A for programmers"
```

**Option B — Python directly (requires Python 3.14+):**

```bash
pip install -r requirements.txt
python download.py \
  --domain stackoverflow.com \
  --title "Stack Overflow" \
  --description "Q&A for programmers"
```

This downloads XML dumps from the default mirror (`https://archive.org/download/stackexchange`), converts them to ZIM format, and writes the file to `./data/`. Stack Overflow is very large — plan for tens of gigabytes of disk space and several hours of processing time.

**Options:**

| Flag | Default | Description |
| --- | --- | --- |
| `--domain` | _(required)_ | Stack Exchange site domain (e.g. `stackoverflow.com`, `cooking.stackexchange.com`) |
| `--title` | _(required)_ | ZIM title (max 30 characters) |
| `--description` | _(required)_ | ZIM description (max 80 characters) |
| `--mirror` | `https://archive.org/download/stackexchange` | Mirror URL for XML dumps |
| `--threads` | sotoki default (1) | Worker threads |
| `--without-images` | off | Exclude images to reduce ZIM size |
| `--debug` | off | Verbose output |

**Note:** sotoki fetches live Stack Exchange URLs during initialization and ZIM conversion (favicons, images). Cloudflare blocks requests that don't present a real browser TLS fingerprint — a browser User-Agent alone is not enough. `sotoki_wrapper.py` handles this automatically by routing all HTTP through `curl_cffi`, which uses BoringSSL to impersonate Firefox at the TLS layer. It also injects a `Referer` header required by Stack Exchange CDNs for sub-resource requests. This is invoked automatically by `download.py` and requires no manual action.

## Converting a Local Dump

If you already have a Stack Exchange 7z dump on disk (e.g. from [archive.org/details/stackexchange](https://archive.org/details/stackexchange)), use `convert.py` to convert it to ZIM without re-downloading.

Place the dump in `./input/` — the filename must be `{domain}.7z` (e.g. `stackoverflow.com.7z`).

**Option A — Docker:**

```bash
docker build -t kiwix-downloader .
docker run --rm -v ./data:/app/data -v ./input:/app/input kiwix-downloader convert \
  --dump /app/input/stackoverflow.com.7z \
  --title "Stack Overflow" \
  --description "Q&A for programmers"
```

**Option B — Python directly:**

```bash
python convert.py \
  --dump ./input/stackoverflow.com.7z \
  --title "Stack Overflow" \
  --description "Q&A for programmers"
```

`convert.py` serves the dump directory over a temporary localhost HTTP server and passes that as the mirror URL to sotoki — no changes to sotoki internals required.

**Options:**

| Flag | Default | Description |
| --- | --- | --- |
| `--dump` | _(required)_ | Path to local `.7z` dump file |
| `--domain` | inferred from filename | Stack Exchange domain (e.g. `stackoverflow.com`) |
| `--title` | _(required)_ | ZIM title (max 30 characters) |
| `--description` | _(required)_ | ZIM description (max 80 characters) |
| `--threads` | sotoki default (1) | Worker threads |
| `--without-images` | off | Exclude images to reduce ZIM size |
| `--debug` | off | Verbose output |

**Note:** sotoki still fetches favicons, CSS, and images from live Stack Exchange URLs during conversion. An internet connection is still needed; use `--without-images` to minimize external requests.

Once the conversion completes, restart kiwix-serve to pick up the new file:

```bash
docker compose restart
```

## Stopping

```bash
docker compose down
```
