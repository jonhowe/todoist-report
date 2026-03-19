import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None


API_KEY_ENV_VAR = "TODOIST_API_KEY"
PROJECT_NAME_ENV_VAR = "TODOIST_PROJECT_NAME"
DEFAULT_PROJECT_NAME = "work"
PROJECTS_URL = "https://api.todoist.com/api/v1/projects"
COMPLETED_TASKS_URL = "https://api.todoist.com/api/v1/tasks/completed/by_completion_date"
REQUEST_TIMEOUT_SECONDS = 30
PAGE_SIZE = 100
ENV_FILE = Path(__file__).resolve().with_name(".env")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Todoist completed-task report for a project."
    )
    parser.add_argument(
        "--project",
        help=(
            f"Todoist project name. Defaults to {PROJECT_NAME_ENV_VAR} or "
            f"'{DEFAULT_PROJECT_NAME}'."
        ),
    )
    parser.add_argument(
        "--since",
        help="Start of the reporting window in UTC. Accepts YYYY-MM-DD or ISO 8601.",
    )
    parser.add_argument(
        "--until",
        help="End of the reporting window in UTC. Accepts YYYY-MM-DD or ISO 8601.",
    )
    parser.add_argument(
        "--output",
        choices=("auto", "table", "plain"),
        default="auto",
        help="Output format. 'auto' uses tabulate when available.",
    )
    return parser.parse_args()


def load_local_env():
    """Load simple KEY=VALUE pairs from .env without extra dependencies."""
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def parse_date(date_str):
    """Attempt to parse a Todoist date string with or without fractional seconds."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_api_key():
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if api_key:
        return api_key

    print(
        f"Error: set {API_KEY_ENV_VAR} in your environment or in {ENV_FILE.name}.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def get_project_name(project_name_override=None):
    if project_name_override is not None:
        project_name = project_name_override.strip().lower()
    else:
        project_name = os.environ.get(PROJECT_NAME_ENV_VAR, DEFAULT_PROJECT_NAME).strip().lower()

    if project_name:
        return project_name

    print(f"Error: {PROJECT_NAME_ENV_VAR} cannot be empty.", file=sys.stderr)
    raise SystemExit(1)


def get_start_of_week_utc():
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)


def format_utc_timestamp(timestamp):
    return timestamp.isoformat().replace("+00:00", "Z")


def parse_datetime_arg(value, argument_name, is_end=False):
    try:
        if len(value) == 10:
            parsed = datetime.strptime(value, "%Y-%m-%d")
            if is_end:
                parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
            return parsed.replace(tzinfo=timezone.utc)

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        print(
            f"Error: --{argument_name} must be YYYY-MM-DD or an ISO 8601 timestamp.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def get_report_window(since_override=None, until_override=None):
    now = datetime.now(timezone.utc)
    since = parse_datetime_arg(since_override, "since") if since_override else get_start_of_week_utc()
    until = parse_datetime_arg(until_override, "until", is_end=True) if until_override else now

    if since > until:
        print("Error: --since must be earlier than or equal to --until.", file=sys.stderr)
        raise SystemExit(1)

    return format_utc_timestamp(since), format_utc_timestamp(until)


def fetch_projects(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    projects = {}
    cursor = None

    while True:
        params = {"limit": PAGE_SIZE}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            PROJECTS_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        payload = response.json()
        for project in payload.get("results", []):
            projects[project.get("name", "").lower()] = project.get("id")

        cursor = payload.get("next_cursor")
        if not cursor:
            return projects


def fetch_completed_tasks(api_key, project_id, since_str, until_str):
    headers = {"Authorization": f"Bearer {api_key}"}
    tasks = []
    cursor = None

    while True:
        params = {
            "since": since_str,
            "until": until_str,
            "limit": PAGE_SIZE,
            "project_id": project_id,
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            COMPLETED_TASKS_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        payload = response.json()
        tasks.extend(payload.get("items", []))

        cursor = payload.get("next_cursor")
        if not cursor:
            return tasks


def format_request_exception(exc):
    response = getattr(exc, "response", None)
    if response is not None and response.status_code == 410:
        return f"{exc} (Todoist reported this endpoint is gone; the API version may need updating.)"
    return str(exc)


def build_table_data(tasks, project_id):
    table_data = []

    for task in tasks:
        if task.get("project_id") != project_id:
            continue

        completed_date_str = task.get("completed_at")
        created_date_str = task.get("added_at") or task.get("created_at")
        task_details = task.get("content", "N/A")

        date_completed = parse_date(completed_date_str)
        date_created = parse_date(created_date_str)

        date_completed_formatted = (
            date_completed.strftime("%Y-%m-%d %H:%M") if date_completed else "N/A"
        )
        date_created_formatted = (
            date_created.strftime("%Y-%m-%d %H:%M") if date_created else "N/A"
        )

        if date_completed and date_created:
            time_open = date_completed - date_created
            total_seconds = int(time_open.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_open_formatted = f"{hours}h {minutes}m {seconds}s"
        else:
            time_open_formatted = "N/A"

        table_data.append(
            [
                date_completed_formatted,
                task_details,
                date_created_formatted,
                time_open_formatted,
            ]
        )

    return table_data


def print_report(table_data, output_format):
    headers = [
        "Date Completed",
        "Task Details",
        "Date Created",
        "Time Task Was Open",
    ]

    if not table_data:
        print("No completed tasks found for the selected project and time window.")
        return

    if output_format == "table" and not tabulate:
        print("Error: table output requires the optional 'tabulate' dependency.", file=sys.stderr)
        raise SystemExit(1)

    table_renderer = tabulate
    if output_format == "table" or (output_format == "auto" and table_renderer):
        if table_renderer is None:
            print("Error: table output requires the optional 'tabulate' dependency.", file=sys.stderr)
            raise SystemExit(1)
        print(table_renderer(table_data, headers=headers, tablefmt="grid"))
        return

    header_row = " | ".join(headers)
    print(header_row)
    print("-" * len(header_row))
    for row in table_data:
        print(" | ".join(row))


def main():
    load_local_env()
    args = parse_args()

    api_key = get_api_key()
    project_name = get_project_name(args.project)
    since_str, until_str = get_report_window(args.since, args.until)

    try:
        projects = fetch_projects(api_key)
        work_project_id = projects.get(project_name)
        if not work_project_id:
            print(
                f"Error: '{project_name}' project not found in your Todoist projects.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        tasks = fetch_completed_tasks(api_key, work_project_id, since_str, until_str)
    except requests.RequestException as exc:
        print(f"Error talking to Todoist API: {format_request_exception(exc)}", file=sys.stderr)
        raise SystemExit(1) from exc

    print_report(build_table_data(tasks, work_project_id), args.output)


if __name__ == "__main__":
    main()
