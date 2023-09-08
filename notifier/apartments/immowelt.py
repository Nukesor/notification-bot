import traceback
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from telegram.error import NetworkError, TimedOut
from telegram.ext import CallbackContext

from notifier.logging import logger
from notifier.notify import send_offers
from notifier.offer import Offer

headers = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        + "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "www.immowelt.de",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}


async def scrape_immowelt(context: CallbackContext) -> None:
    """This is a high level wrapper around the actual scraper logic.

    It's purpose is to allow easy global error handling.
    """
    try:
        logger.info("Checking Immowelt")
        await scrape_inner(context)
    except Exception as ex:
        # Ignore telegram network errors
        if type(ex) is TimedOut or type(ex) is NetworkError:
            return

        logger.error(f"Got exception {ex}")
        traceback.print_exc()
        # await context.bot.sendMessage(
        #    chat_id=config["telegram"]["target_channel"],
        #    text=f"Scraper failed with exception {ex}",
        # )
        return


async def scrape_inner(context: CallbackContext) -> None:
    """Scrape Immowelt and send regular updates on new events."""

    # Load the side with the our current search criteria
    url = (
        "https://www.immowelt.de/suche/hamburg/wohnungen/mieten"
        + "?ami=65&d=true&ffs=FITTED_KITCHEN&pma=1500&rmi=3&sd=DESC&sf=TIMESTAMP&sp=1"
    )
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.warn(f"Got response with status code {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the element that contains all offers
    container = soup.select('div[class*="SearchResults-"]')
    if len(container) == 0:
        logger.error("Failed to get offer container. Please investigate.")
        return

    container = container[0]
    offer_items = container.select('div[class*="EstateItem-"]')

    if offer_items is None:
        logger.error("Failed to get list of offers from container. Please investigate.")
        return

    # Iterate through all offers and extract all interesting information.
    offers = []
    for raw_offer in offer_items:
        try:
            offer = extract_offer_details(raw_offer)

            # There're some list items that aren't offers
            if offer is None:
                continue

            offers.append(offer)
        except Exception as ex:
            logger.error(f"Got exception {ex} for the following block:")
            logger.error(raw_offer.prettify())

            raise ex

    import pprint

    pprint.pprint(offers)

    # await send_offers(context.bot, offers)


def extract_offer_details(raw_offer) -> Offer | None:
    offer = Offer()
    offer.source = "Immowelt"
    # There's no time info on offers from immowelt
    offer.raw_time = "vor ca. 5min"
    offer.time = None

    # The offer is a single large link, which contains all other infos.
    link = raw_offer.find("a")

    # Get the link for this offer
    offer.link = link.attrs["href"]

    # The id of the offer is the very last item of the link
    offer.id = offer.link.split("/")[-1]

    # All interesting information is contained in a `FactsMain` div.
    facts_main = link.select('div[class*="FactsMain-"]')[0]

    # Get some infos for the appartment (size, price, rooms)
    key_facts = facts_main.select('div[class*="KeyFacts-"] > div')
    for child in key_facts:
        # Explicitly handle the price
        if child.attrs["data-test"] == "price":
            offer.price = child.get_text().strip()
            continue

        offer.key_data.append(child.get_text().strip())

    # Get the title for the offer
    offer.title = facts_main.find("h2").get_text().strip()

    # Get the estate detail wrapper
    facts = facts_main.select('div > div > div[class*="IconFact-"]')

    for fact in facts:
        fact_name = fact.find("i").get_text().strip()
        fact_text = fact.find("span").get_text().strip()
        if fact_name == "location":
            offer.location = fact_text
        elif fact_name == "check":
            # Get the list of equipment. Filter out the `...` item.
            equipment = fact_text.split(", ")
            offer.equipment = list(filter(lambda x: x != "...", equipment))

    return offer
