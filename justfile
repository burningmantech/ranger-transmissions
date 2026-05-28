MODULE_NAME := "transmissions"

default:
  @just --list

lint:
    uv run --group=lint pre-commit run --all-files

mypy TARGET="src":
    uv run --group=mypy mypy "{{TARGET}}"

test TARGET=MODULE_NAME:
    uv run --group=unit trial --random=0 --jobs=2 "{{TARGET}}"

_coverage *args:
    uv run --group=unit coverage {{args}}

@coverage TARGET=MODULE_NAME:
    just _coverage run --source="{{MODULE_NAME}}" -m twisted.trial --random=0 --jobs=2 "{{TARGET}}"
    just _coverage combine
    just _coverage xml
    just _coverage report --skip-covered

@coverage_report:
    just _coverage report
    just _coverage html

packaging:
    uv run --group=packaging pip wheel --no-deps --wheel-dir=dist .
    uv run --group=packaging twine check dist/*

doit: lint mypy coverage

serve:
    uv run rtx web

_http *args:
    uvx --from httpie http {{args}}

request path="" *args:
    @just _http {{args}} http://localhost:8080/{{path}}

browser:
    uv run -m webbrowser -t http://localhost:8080/
