from telegram.ext import Application, ContextTypes
from telegram.error import NetworkError, TimedOut

from notifier.config import config
from notifier.apartments.kleinanzeigen import scrape


def init_telegram():
    # Initialize telegram updater and application
    app = (
        Application.builder()
        .token(config["telegram"]["api_key"])
        .concurrent_updates(5)
        .build()
    )

    app.add_error_handler(error_handler)

    job_queue = app.job_queue
    job_queue.run_repeating(
        scrape,
        interval=5 * 60,
        first=2,
        name="Remove old data",
    )

    return app


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ignore any errors."""

    # Ignore telegram network errors
    ex = context.error
    if ex is None:
        return

    if type(ex) is TimedOut or type(ex) is NetworkError:
        return

    # Raise all other exceptions
    raise ex
