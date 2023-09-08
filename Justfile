default: run

run:
    poetry run python main.py run

setup:
    poetry install

lint:
    poetry run black --check notifier
    poetry run isort \
        --skip __init__.py \
        --check-only notifier
    poetry run flake8 notifier

format:
    # remove unused imports
    poetry run autoflake \
        --remove-all-unused-imports \
        --recursive \
        --exclude=__init__.py,.venv \
        --in-place notifier
    poetry run black notifier
    poetry run isort notifier \
        --skip __init__.py


# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
