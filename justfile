# just docs: https://just.systems/man/en/

MODULE_NAME := "transmissions"

@_default:
  just --list

# Run linters and formatters
[group("qa")]
lint:
    uv tool run pre-commit run --all-files

# Run unit tests
[group("qa")]
test:
    @just trial

# Run unit tests with coverage
[group("qa")]
coverage:
    @just trial_coverage

# Run all checks
[group("qa")]
doit: lint typing coverage

# Generate coverage report
[group("qa")]
@coverage_report:
    @just _trial_coverage report
    @just _trial_coverage html

#
# Python
#

# Helper for running commands via uv
_uvrun *args:
    uv --directory=python run {{args}}

# Run Python
[group("dev")]
python *args:
    @just _uvrun python {{args}}

# Run mypy
[group("qa")]
mypy TARGET="src":
    @just _uvrun --group=mypy mypy "{{TARGET}}"

# Run type checks
[group("qa")]
typing:
    @just mypy

# Run tests
[group("qa")]
trial TARGET=MODULE_NAME:
    @just _uvrun --group=unit trial --random=0 --jobs=2 "{{TARGET}}"

# Helper for running trial with coverage
_trial_coverage *args:
    @just _uvrun --group=unit coverage {{args}}

# Run tests with coverage
[group("qa")]
@trial_coverage TARGET=MODULE_NAME:
    @just _trial_coverage run --source="{{MODULE_NAME}}" -m twisted.trial --random=0 --jobs=2 "{{TARGET}}"
    @just _trial_coverage combine
    @just _trial_coverage xml
    @just _trial_coverage report --skip-covered

# Check packaging
[group("qa")]
packaging:
    @just _uvrun --group=packaging pip wheel --no-deps --wheel-dir=dist .
    @just _uvrun --group=packaging twine check dist/*

# Update lockfile
[group("lifecycle")]
update:
    uv lock --upgrade

# Install dependencies
[group("lifecycle")]
install:
    uv --directory=python sync

# Run indexer
[group("run")]
index *args:
    @just _uvrun rtx index {{args}}

# Run the web server
[group("run")]
serve:
    _uvrun rtx web

# Helper for running httpie
_http *args:
    uvx --from httpie http {{args}}

# Make an HTTP request to the local server
[group("run")]
request path="" *args:
    @just _http {{args}} http://localhost:8080/{{path}}

# Open the local server in the default web browser
[group("run")]
browser:
    @just _uvrun -m webbrowser -t http://localhost:8080/
