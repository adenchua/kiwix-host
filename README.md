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

**Option B — Python directly:**

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

Once the download completes, restart kiwix-serve to pick up the new file:

```bash
docker compose restart
```

## Stopping

```bash
docker compose down
```
