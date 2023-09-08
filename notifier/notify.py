import os
import time

from telegram import Bot
from telegram.constants import ParseMode

from notifier.config import config
from notifier.offer import Offer

known_ids_path = os.path.expanduser("~/.local/share/notifier_known_ids")


async def send_offers(bot: Bot, offers: list[Offer]) -> None:
    """Get a list of offers and send them.

    We do some additional checks in here to only send offers that are viable to us.
    We also make sure that we don't send offers twice.
    """

    # Get the list of all ids that we already sent
    known_ids = []
    if os.path.exists(known_ids_path):
        with open(known_ids_path, "r") as reader:
            text = reader.read().strip()
            known_ids = text.split("\n")

    for offer in offers:
        # Don't send offers twice
        if offer.id in known_ids:
            continue

        # Ignore offers that don't match our criteria
        if not offer.is_viable():
            known_ids.append(offer.id)
            continue

        await bot.sendMessage(
            chat_id=config["telegram"]["target_channel"],
            text=offer.format(),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

        time.sleep(2)

        known_ids.append(offer.id)

    # Write the known_ids file back to disk
    with open(known_ids_path, "w") as descriptor:
        descriptor.write("\n".join(known_ids))
