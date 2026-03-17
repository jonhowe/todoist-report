# todoist-report

Generate a report of completed Todoist tasks for a project since the start of the current week.

## Setup

1. Create and activate a virtual environment if you want one.
2. Install dependencies with `python3 -m pip install -r requirements.txt`.
3. Provide credentials with shell environment variables or a local `.env` file.

The script reads `.env` from the repository root if present. See `.env.example` for the expected variable names.

## Configuration

- `TODOIST_API_KEY`: required Todoist API token.
- `TODOIST_PROJECT_NAME`: optional project name to report on. Defaults to `work`.

## Usage

Run:

```bash
python3 todoist_report.py
```

If `tabulate` is installed, the output is rendered as a table. Otherwise the script falls back to plain text columns.
