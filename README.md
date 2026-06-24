# misp-export

A minimal, standalone CLI tool to export all events from a [MISP](https://www.misp-project.org/) instance to a JSON file - ready for SIEM ingestion or sharing.

It retrieves every event visible to your API key (with full attributes and objects) via the MISP REST API and writes them to a single JSON file.

## Why it's minimal

- **Standard library + `requests` only** - no `pymisp`, `click`, or `rich`.
- **No auto-update, no subprocess calls** - the tool never shells out or contacts anything other than your configured MISP URL.
- Paginated REST calls so large instances export reliably.
- Single-file (`main.py`) implementation that is easy to read and audit.

## Requirements

- Python 3.8+
- Dependencies in [requirements.txt](requirements.txt)

## Installation

```bash
git clone https://github.com/mispquickshareorg/misp-export.git
cd misp-export
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and fill in your MISP details:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISP_URL` | Yes | - | Base URL of your MISP instance (`https://...`) |
| `MISP_API_KEY` | Yes | - | Your MISP API authentication key |
| `MISP_VERIFY_SSL` | No | `true` | Set to `false` for self-signed certificates |
| `MISP_TIMEOUT` | No | `120` | Request timeout in seconds |

> **Note:** `.env` is git-ignored. Never commit real credentials.

## Usage

```bash
# Export to an auto-timestamped file (misp_events_export_YYYY-MM-DD_HHMMSS.json)
python main.py

# Export to a specific file
python main.py --output events.json

# Pretty-print the JSON
python main.py --output events.json --pretty

# Use a specific env file
python main.py --env-file /path/to/.env
```

The tool prints a summary (event / attribute / object counts and file size) and exits `0` on success, `1` on failure.

## Security notes

- The export contains **all events visible to your API key**. Review the output and consider filtering by TLP level before sharing externally.
- The API key is read from the environment only and is never logged.
- The only network destination is the `MISP_URL` you configure.
- Export output files (`misp_events_export_*.json`) are git-ignored to avoid accidentally committing intelligence data.

## License

MIT
