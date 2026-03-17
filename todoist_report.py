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
PROJECTS_URL = "https://api.todoist.com/rest/v1/projects"
COMPLETED_TASKS_URL = "https://api.todoist.com/sync/v9/completed/get_all"
REQUEST_TIMEOUT_SECONDS = 30
ENV_FILE = Path(__file__).resolve().with_name(".env")


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


def get_project_name():
    project_name = os.environ.get(PROJECT_NAME_ENV_VAR, DEFAULT_PROJECT_NAME).strip().lower()
    if project_name:
        return project_name

    print(f"Error: {PROJECT_NAME_ENV_VAR} cannot be empty.", file=sys.stderr)
    raise SystemExit(1)


def get_start_of_week_utc():
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)


def fetch_projects(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(PROJECTS_URL, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    return {
        project.get("name", "").lower(): project.get("id")
        for project in response.json()
    }


def fetch_completed_tasks(api_key, since_str):
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "since": since_str,
        "limit": 100,
    }
    response = requests.get(
        COMPLETED_TASKS_URL,
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json().get("items", [])


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


def print_report(table_data):
    headers = [
        "Date Completed",
        "Task Details",
        "Date Created",
        "Time Task Was Open",
    ]

    if tabulate:
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        return

    header_row = " | ".join(headers)
    print(header_row)
    print("-" * len(header_row))
    for row in table_data:
        print(" | ".join(row))


def main():
    load_local_env()

    api_key = get_api_key()
    project_name = get_project_name()
    since_str = get_start_of_week_utc().isoformat().replace("+00:00", "Z")

    try:
        projects = fetch_projects(api_key)
        work_project_id = projects.get(project_name)
        if not work_project_id:
            print(
                f"Error: '{project_name}' project not found in your Todoist projects.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        tasks = fetch_completed_tasks(api_key, since_str)
    except requests.RequestException as exc:
        print(f"Error talking to Todoist API: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print_report(build_table_data(tasks, work_project_id))


if __name__ == "__main__":
    main()
