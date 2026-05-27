default:
  @just --list

lint:
    pre-commit run --all-files

mypy TARGET="src":
    uv run --group=mypy mypy "{{TARGET}}"

test TARGET="transmissions":
    uv run --group=unit trial --random=0 --jobs=2 "{{TARGET}}"

coverage TARGET="transmissions":
    uv run --group=unit coverage run --source="transmissions" -m twisted.trial --random=0 --jobs=2 "{{TARGET}}"
    uv run --group=unit coverage combine
    uv run --group=unit coverage xml
    uv run --group=unit coverage report --skip-covered

coverage_report:
    uv run --group=unit coverage report
    uv run --group=unit coverage html

packaging:
    uv run --group=packaging pip wheel --no-deps --wheel-dir=dist .
    uv run --group=packaging twine check dist/*
