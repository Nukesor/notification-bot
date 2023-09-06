from telegram.ext import Application

from scraper.config import config
from scraper.kleinanzeigen import scrape


def init_telegram():
    # Initialize telegram updater and application
    app = (
        Application.builder()
        .token(config["telegram"]["api_key"])
        .concurrent_updates(5)
        .build()
    )

    job_queue = app.job_queue
    job_queue.run_repeating(
        scrape,
        interval=5 * 60,
        first=2,
        name="Remove old data",
    )

    return app
