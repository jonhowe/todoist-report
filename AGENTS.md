# AGENTS.md
Guidance for coding agents working in `todoist-report`.

## Repo Snapshot
- Main script: `todoist_report.py`
- Dependencies: `requirements.txt`
- Env example: `.env.example`
- Human docs: `README.md`
- Structure is a small single-file CLI utility

## Existing Rules
- No prior `AGENTS.md` was present
- No `.cursorrules` file exists
- No files exist under `.cursor/rules/`
- No `.github/copilot-instructions.md` file exists
- Follow this file and the existing style in `todoist_report.py`

## Setup
Use `python3` unless the active environment clearly requires another executable.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Use `.env.example` as the reference for local credentials.

## Key Commands
Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the script:

```bash
python3 todoist_report.py
python3 todoist_report.py --project Work --since 2026-03-01 --until 2026-03-07 --output plain
```

Syntax verification:

```bash
python3 -m py_compile todoist_report.py
```

## Build / Lint / Test Status
- No formal build system is configured
- No lint tool is configured in-repo
- No formatter config is checked in
- No automated tests are checked in today
- Prefer the lightest accurate validation command for the task

## Build Commands
There is no artifact build step. Use Python compilation as the closest equivalent.

```bash
python3 -m py_compile todoist_report.py
```

## Lint Commands
No lint command exists in the repository.
Fallback sanity check:

```bash
python3 -m py_compile todoist_report.py
```

Do not assume `ruff`, `flake8`, `pylint`, `black`, `mypy`, or `tox` are available unless you add them.

## Test Commands
There are no current automated tests.
Useful validation commands:

```bash
python3 -m py_compile todoist_report.py
python3 todoist_report.py
```

Running the script requires valid Todoist credentials in the environment or a local `.env` file.

## Single-Test Commands
There is no true single-test command yet because there is no test suite.
If you add `pytest` tests in a future change, use standard single-test forms:

```bash
pytest tests/test_file.py
pytest tests/test_file.py::test_name
pytest tests/test_file.py -k test_name
```

Only rely on those commands after tests actually exist.

## Runtime Configuration
The script uses:
- `TODOIST_API_KEY`: required
- `TODOIST_PROJECT_NAME`: optional, defaults to `work`

It also reads a root-level `.env` file if present.

## Current CLI Parameters
- `--project`: overrides the configured project name for one run
- `--since`: sets the report start in UTC; accepts `YYYY-MM-DD` or ISO 8601
- `--until`: sets the report end in UTC; accepts `YYYY-MM-DD` or ISO 8601
- `--output`: chooses `auto`, `table`, or `plain`
- Default behavior without flags remains: current UTC week, configured project, automatic output mode

## Current API Usage
- Projects are fetched from Todoist `GET /api/v1/projects`
- Completed tasks are fetched from Todoist `GET /api/v1/tasks/completed/by_completion_date`
- Both endpoints are paginated and use `next_cursor`
- Avoid reintroducing deprecated Todoist `rest/v1` or `sync/v9/completed/get_all` endpoints
- The completed-task request currently sends `since`, `until`, `limit`, and `project_id`

## File Responsibilities
- `todoist_report.py`: env loading, API requests, filtering, formatting, CLI flow
- `requirements.txt`: third-party dependencies
- `.env.example`: expected configuration values
- `README.md`: setup and usage notes

## Code Style
Match the existing code unless the user asks for broader cleanup.

## Imports
- Order imports as standard library, blank line, third-party
- Keep imports explicit and minimal
- Remove unused imports
- Use narrow `try/except ImportError` blocks only for truly optional dependencies

## Formatting
- Follow normal PEP 8 conventions
- Use 4-space indentation
- Keep lines readable and similar in style to the existing file
- Separate top-level functions with blank lines
- Prefer simple, readable code over compact clever code

## Types
- The current codebase does not use type annotations
- Do not add pervasive type hints unless they improve the changed code
- If adding types, keep them lightweight and consistent
- Avoid typing-heavy patterns without a clear payoff

## Naming
- Use `snake_case` for functions and variables
- Use `UPPER_SNAKE_CASE` for constants
- Prefer descriptive domain names like `project_name` and `completed_date_str`
- Avoid vague names like `data` when a more specific name fits

## Function Design
- Keep functions focused on one job
- Prefer helpers for parsing, API access, formatting, and env handling
- Keep `main()` as the orchestration layer
- Pass resolved values into helpers instead of expanding global state
- Avoid class abstractions unless the task clearly needs them

## Error Handling
- Fail fast for missing required configuration
- Print user-facing errors to `stderr`
- Exit CLI failures with `raise SystemExit(1)`
- Catch `requests.RequestException` at a practical boundary
- Preserve exception chains when re-raising
- Do not silently swallow API or parsing failures without a real fallback

## HTTP Conventions
- Always use a timeout for network calls
- Keep API URLs and timeout values in named constants
- Call `response.raise_for_status()` before using the response body
- Keep headers and params explicit near the request call
- Preserve pagination handling when working with Todoist `api/v1` list endpoints
- Avoid retries, sessions, or caching unless the task requires them

## Configuration Conventions
- Keep env var names in module constants
- Read config once, then pass values downward
- Preserve `.env` compatibility unless the user requests a change
- Avoid extra config libraries unless they solve a real problem

## Output Conventions
- Preserve the CLI-first behavior
- Keep output readable with and without `tabulate`
- Keep date formatting deterministic
- Ensure fallback plain-text output works without optional dependencies
- Preserve the current empty-result message: `No completed tasks found for the selected project and time window.` unless the user asks to change it
- Preserve the `--output` flag semantics when changing report rendering

## Dependencies
- Keep dependencies minimal
- Prefer the standard library when practical
- If you add a dependency, update `requirements.txt`
- If behavior changes, update `README.md` and this file when relevant

## Future Testing Guidance
- Favor pure helper functions when adding logic so they are easy to test
- If tests are added, prefer `pytest`
- Focus tests on date parsing, env loading, filtering, and output shaping
- Mock Todoist API calls instead of using the live service in automated tests

## Agent Behavior
- Make the smallest change that fully solves the task
- Do not invent commands that are not present in the repo
- Verify commands from checked-in files before documenting them
- Treat this as a lightweight utility rather than a framework app
- Prefer incremental improvement over architectural rewrites
- Keep docs and examples aligned with actual behavior

## Practical Workflow
- Read `README.md`, `requirements.txt`, and `todoist_report.py` before editing
- Prefer verifying with `python3 -m py_compile todoist_report.py` after code changes
- Run `python3 todoist_report.py` only when credentials are available or the task requires runtime validation
- Keep user-facing behavior stable unless the request clearly asks for a change
- If you add tests or tooling, update this file with the exact verified commands

## Change Scope Guidelines
- Prefer targeted edits over broad rewrites
- Avoid renaming public behavior or env vars without a user request
- Keep optional dependency behavior intact unless intentionally changing it
- Preserve fallback output behavior when `tabulate` is unavailable
- Update `.env.example` when configuration expectations change

## Good Candidates for Refactoring
- Repeated parsing or formatting logic
- API request handling that needs stronger reuse
- Output shaping that benefits from pure helper functions
- Validation logic that can be isolated from network calls
- Small readability improvements that do not change CLI behavior
