import traceback

from telegram.error import NetworkError, TimedOut
from telegram.ext import CallbackContext

from notifier.logging import logger
from .immowelt import scrape_immowelt
from .kleinanzeigen import scrape_kleinanzeigen


async def scrape(context: CallbackContext) -> None:
    """This is a high level wrapper around the actual scraper logic.

    It's purpose is to allow easy global error handling.
    """

    try:
        logger.info("Checking Immowelt")
        await scrape_immowelt(context)
    except Exception as ex:
        # Ignore telegram network errors
        if type(ex) is TimedOut or type(ex) is NetworkError:
            pass
        else:
            logger.error(f"Got exception {ex}")
            traceback.print_exc()
            # await context.bot.sendMessage(
            #    chat_id=config["telegram"]["target_channel"],
            #    text=f"Scraper failed with exception {ex}",
            # )
            pass

    try:
        logger.info("Checking Kleinanzeigen")
        await scrape_kleinanzeigen(context)
    except Exception as ex:
        # Ignore telegram network errors
        if type(ex) is TimedOut or type(ex) is NetworkError:
            pass
        else:
            logger.error(f"Got exception {ex}")
            traceback.print_exc()
            # await context.bot.sendMessage(
            #    chat_id=config["telegram"]["target_channel"],
            #    text=f"Scraper failed with exception {ex}",
            # )
            pass
