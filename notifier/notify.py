import time

from telegram import Bot
from telegram.constants import ParseMode

from notifier.apartments.offer import Apartment
from notifier.config import config
from notifier.known_keys import KnownKeys
from notifier.logging import logger


async def send_apartment_offers(bot: Bot, offers: list[Apartment]) -> None:
    """Get a list of offers and send them.

    We do some additional checks in here to only send offers that are viable to us.
    We also make sure that we don't send offers twice.
    """
    known_keys = KnownKeys()
    known_keys.read_from_disk()

    for offer in offers:
        # Don't send offers twice
        if known_keys.has_key(offer.source, offer.id):
            continue

        # Ignore offers that don't match our criteria
        if not offer.is_viable():
            known_keys.add_key(offer.source, offer.id)
            continue

        logger.info(f"Sending notification for: {offer.title}")
        # Send the notification
        await bot.sendMessage(
            chat_id=config["telegram"]["target_channel"],
            text=offer.format(),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

        time.sleep(2)

        known_keys.add_key(offer.source, offer.id)
        known_keys.write_to_disk()

    known_keys.write_to_disk()
