# todoist-report

`todoist-report` is a small command-line utility that fetches completed tasks from Todoist for a single project and prints a weekly completion report.

It is designed for a simple workflow:

- look up one Todoist project by name
- fetch tasks completed for that project during the current UTC week
- show when each task was created, when it was completed, and how long it remained open

The repository is intentionally lightweight. There is one main Python script, minimal dependencies, and no heavy framework or packaging setup.

## What the project does

When you run `python3 todoist_report.py`, the script:

1. loads environment variables from your shell and an optional local `.env` file
2. reads the target Todoist project name from configuration
3. calculates the start of the current week in UTC
4. fetches your Todoist projects from Todoist's current `api/v1` endpoint
5. finds the configured project by name
6. fetches completed tasks for that project from the start of the current week until now
7. prints a report showing:
   - completion timestamp
   - task content
   - creation timestamp
   - total time the task was open

## Repository layout

- `todoist_report.py`: main script and all application logic
- `requirements.txt`: third-party dependencies
- `.env.example`: example environment configuration
- `AGENTS.md`: guidance for coding agents working in this repository

## Requirements

- Python 3
- A Todoist API token
- Network access to Todoist APIs

Dependencies currently used:

- `requests`: required for API calls
- `tabulate`: optional nicer table rendering; the script falls back to plain text if it is unavailable

## Setup

Create and activate a virtual environment if you want one, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configuration

The script reads configuration from shell environment variables and also loads a root-level `.env` file if present.

### Supported variables

- `TODOIST_API_KEY`: required Todoist personal API token
- `TODOIST_PROJECT_NAME`: optional project name to report on; defaults to `work`

### Example `.env`

```dotenv
TODOIST_API_KEY=your_todoist_api_token_here
TODOIST_PROJECT_NAME=work
```

See `.env.example` for the checked-in example.

## Parameters and behavior

The script is configured primarily through environment variables, with optional command-line flags for per-run overrides.

### Command-line flags

- `--project`: overrides `TODOIST_PROJECT_NAME` for the current run
- `--since`: sets the start of the reporting window; accepts `YYYY-MM-DD` or an ISO 8601 timestamp
- `--until`: sets the end of the reporting window; accepts `YYYY-MM-DD` or an ISO 8601 timestamp
- `--output`: chooses output format; valid values are `auto`, `table`, and `plain`

Examples:

```bash
python3 todoist_report.py --project Work
python3 todoist_report.py --since 2026-03-01 --until 2026-03-07
python3 todoist_report.py --project Work --since 2026-03-01T00:00:00Z --until 2026-03-07T23:59:59Z
python3 todoist_report.py --output plain
```

### `TODOIST_API_KEY`

- Required: yes
- Purpose: authenticates requests to Todoist
- Source: environment variable or local `.env`
- Failure mode: if missing, the script prints an error to `stderr` and exits with status code `1`

### `TODOIST_PROJECT_NAME`

- Required: no
- Default: `work`
- Purpose: chooses the Todoist project to report on
- Matching behavior: the script lowercases both the configured name and Todoist project names before matching
- Failure mode: if the configured project is blank or not found, the script prints an error to `stderr` and exits with status code `1`

### Time window

- Start: beginning of the current week in UTC, with Monday as the first day
- End: current time in UTC when the script runs
- Scope: only completed tasks in that window are requested from Todoist
- Override support: `--since` and `--until` can replace the default weekly window for a single run

### Output format

- Default: `auto`
- `auto`: uses `tabulate` when installed, otherwise falls back to plain text
- `table`: requires `tabulate` and exits with an error if it is not installed
- `plain`: always prints the fallback text-table format

### Pagination

- Project lookup uses Todoist's paginated `GET /api/v1/projects` endpoint
- Completed task lookup uses Todoist's paginated `GET /api/v1/tasks/completed/by_completion_date` endpoint
- The script follows `next_cursor` until all pages are fetched

## Usage

Run the script with:

```bash
python3 todoist_report.py
```

You can also override configuration per run, for example:

```bash
python3 todoist_report.py --project Work --since 2026-03-01 --until 2026-03-07 --output plain
```

## Example output

If `tabulate` is installed, the report is printed as a formatted table.

If `tabulate` is not installed, the report falls back to plain text columns like this:

```text
Date Completed | Task Details | Date Created | Time Task Was Open
-----------------------------------------------------------------
2026-03-16 09:12 | Draft weekly notes | 2026-03-15 14:05 | 19h 7m 0s
2026-03-17 11:40 | Review roadmap | 2026-03-17 09:10 | 2h 30m 0s
```

## Report columns

- `Date Completed`: when Todoist reports the task was completed
- `Task Details`: the task content text from Todoist
- `Date Created`: the task creation timestamp; the script prefers `added_at`, then falls back to `created_at`
- `Time Task Was Open`: the difference between creation time and completion time

All displayed timestamps are formatted as `YYYY-MM-DD HH:MM`.

## API details

The script currently uses these Todoist endpoints:

- `GET https://api.todoist.com/api/v1/projects`
- `GET https://api.todoist.com/api/v1/tasks/completed/by_completion_date`

The completed-task request currently sends these parameters:

- `since`
- `until`
- `limit`
- `project_id`
- `cursor` when retrieving additional pages

The script uses a Bearer token in the `Authorization` header and sets a request timeout for all network calls.

## Validation commands

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Syntax check:

```bash
python3 -m py_compile todoist_report.py
```

Run the script:

```bash
python3 todoist_report.py
```

There is currently no formal test suite checked into the repository.

## Current limitations

- The script reports on exactly one project at a time
- The default reporting window is the current UTC week unless overridden with flags
- There is no sorting or filtering configuration beyond the selected project
- There is no automated test suite yet

## Future enhancements

Potential next improvements for this utility include:

- command-line flags for project name, date range, and output format, so the script can be configured per run without changing environment variables.
- custom reporting windows instead of only the current UTC week, which would make the tool more useful for monthly reviews, retrospectives, or ad hoc date ranges.
- exporting reports to CSV or JSON for downstream analysis, so the output can be imported into spreadsheets, dashboards, or other automation.
- optional sorting or grouping by completion date or task age, which would make it easier to scan patterns in how work is being completed.
- friendlier empty-result output such as the current `No completed tasks found for the selected project and time window.` message, which could later be expanded with counts, date ranges, or project context.
- automated tests for date parsing, pagination, and report formatting, which would reduce the risk of future regressions when Todoist APIs or report logic change.
- support for multiple projects in a single run, so one invocation can generate broader weekly reporting across several Todoist projects.

## Error handling and troubleshooting

### Missing API key

If `TODOIST_API_KEY` is missing, the script exits with an error telling you to set it in your environment or local `.env` file.

### Project not found

If `TODOIST_PROJECT_NAME` does not match any of your Todoist projects, the script exits with an error.

Things to check:

- the project name is spelled correctly
- the token belongs to the expected Todoist account
- the project exists and is visible to that account

### Empty report

If no completed tasks are returned for the selected project and reporting window, the script prints `No completed tasks found for the selected project and time window.`

### API failures

If Todoist returns an HTTP error, the script prints the failure to `stderr` and exits with status code `1`.

This can happen if:

- the API token is invalid
- the network request times out
- Todoist is temporarily unavailable
- Todoist deprecates or changes an endpoint

The script includes a clearer message for `410 Gone` responses to make endpoint-version issues easier to diagnose.

## Development notes

This repository is intentionally small and currently has no package structure, test suite, or formal lint setup.

For contributors and coding agents:

- keep changes focused and incremental
- prefer `python3 -m py_compile todoist_report.py` as the first validation step
- update `AGENTS.md` and this README when behavior or required commands change
