default: run

run:
    poetry run python main.py

setup:
    poetry install

lint:
    poetry run black --check pollbot
    poetry run isort \
        --skip __init__.py \
        --check-only pollbot
    poetry run flake8 pollbot

format:
    # remove unused imports
    poetry run autoflake \
        --remove-all-unused-imports \
        --recursive \
        --exclude=__init__.py,.venv \
        --in-place pollbot
    poetry run black pollbot
    poetry run isort pollbot \
        --skip __init__.py


# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
