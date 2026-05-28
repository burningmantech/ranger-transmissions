# just docs: https://just.systems/man/en/

MODULE_NAME := "transmissions"

@_default:
  just --list

# Run linters and formatters
[group("qa")]
lint:
    uv run --group=lint pre-commit run --all-files

# Run type checker
[group("qa")]
typing TARGET="src":
    uv run --group=mypy mypy "{{TARGET}}"

# Run tests
[group("qa")]
test TARGET=MODULE_NAME:
    uv run --group=unit trial --random=0 --jobs=2 "{{TARGET}}"

_coverage *args:
    uv run --group=unit coverage {{args}}

# Run tests with coverage
[group("qa")]
@coverage TARGET=MODULE_NAME:
    just _coverage run --source="{{MODULE_NAME}}" -m twisted.trial --random=0 --jobs=2 "{{TARGET}}"
    just _coverage combine
    just _coverage xml
    just _coverage report --skip-covered

# Generate coverage report
[group("qa")]
@coverage_report:
    just _coverage report
    just _coverage html

# Check packaging
[group("qa")]
packaging:
    uv run --group=packaging pip wheel --no-deps --wheel-dir=dist .
    uv run --group=packaging twine check dist/*

# Run all checks
[group("qa")]
doit: lint typing coverage

# Update lockfile
[group("lifecycle")]
update:
    uv lock --upgrade

# Install dependencies
[group("lifecycle")]
install:
    uv sync

# Run the web server
[group("run")]
serve:
    uv run rtx web

_http *args:
    uvx --from httpie http {{args}}

# Make an HTTP request to the local server
[group("run")]
request path="" *args:
    @just _http {{args}} http://localhost:8080/{{path}}

# Open the local server in the default web browser
[group("run")]
browser:
    uv run -m webbrowser -t http://localhost:8080/
