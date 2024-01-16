default: run

run:
    poetry run python main.py run

setup:
    poetry install

lint:
    poetry run ruff check ./notifier --show-source
    poetry run ruff format ./notifier --diff

format:
    poetry run ruff check --fix ./notifier
    poetry run ruff format ./notifier

# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
