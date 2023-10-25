from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from telegram.ext import CallbackContext

from notifier.logging import logger
from notifier.notify import send_offers
from notifier.offer import Offer

headers = {
    "Accept": (
        "text/html;charset=utf-8,"
        + "application/xhtml+xml;charset=utf-8,"
        + "application/xml;q=0.9;charset=utf-8,"
        + "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "www.kleinanzeigen.de",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}


async def scrape_kleinanzeigen(context: CallbackContext) -> None:
    """Scrape Kleinanzeigen and send regular updates on new events."""

    # Load the side with the our current search criteria
    url = (
        "https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/"
        + "anzeige:angebote/preis::1600/c203l9409+"
        + "wohnung_mieten.qm_d:65%2C+wohnung_mieten.zimmer_d:3%2C5"
    )
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.warn(f"Got response with status code {response.status_code}")

    # For some reason, there's a zero-width whitespace character inserted into
    # some text. This breaks beautiful soup, which is why we remove it.
    text = response.text
    text = text.replace("&#8203", "")

    soup = BeautifulSoup(text, "html.parser")

    # Find the element that contains all offers
    container = soup.select("div.l-container-row.contentbox-unpadded.no-bg")
    if len(container) == 0:
        logger.error("Container is empty. Please investigate.")

    container = container[0]
    if container is None:
        logger.error("Failed to get container. Please investigate.")
        return

    offer_list = container.find("ul")

    if offer_list is None:
        return

    # Iterate through all offers and extract all interesting information.
    offers = []
    for raw_offer in offer_list.find_all("li"):
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

    await send_offers(context.bot, offers)


def extract_offer_details(raw_offer) -> Offer | None:
    offer = Offer()
    offer.source = "Kleinanzeigen"

    # Filter list items that aren't real offers
    if raw_offer.find("article") is None:
        return None

    # Assemble the link for this offer
    offer.link = (
        "https://kleinanzeigen.de" + raw_offer.find("article").attrs["data-href"]
    )

    # The id of the offer is the very last item of the link
    offer.id = offer.link.split("/")[-1]
    offer.location = (
        raw_offer.find(attrs={"class": "aditem-main--top--left"}).get_text().strip()
    )

    # Determine the date this offer has been created at.
    time = raw_offer.find(attrs={"class": "aditem-main--top--right"}).get_text().strip()
    offer.raw_time = time
    if time == "":
        offer.time = None
    else:
        # If there's no `:` inside the time, this is a date and older than two days.
        if ":" not in time:
            offer.time = datetime.strptime(time, "%d.%m.%Y")
        else:
            # Parse a recent offer time, which has these two formats:
            # Gestern, 18:01
            # Heute, 12:15

            # Extract the date part and the hour + minute components
            split = time.split(", ")
            day = split[0]
            [hour, minute] = split[1].split(":")

            # Set the date based on the date string
            offer_date = datetime.now()
            if day == "Gestern":
                offer_date = offer_date - timedelta(days=1)

            # Set the time
            offer.time = offer_date.replace(
                hour=int(hour), minute=int(minute), second=0, microsecond=0
            )

    main_content = raw_offer.find(attrs={"class": "aditem-main--middle"})
    offer.title = main_content.find("h2").get_text().strip()
    offer.description = (
        raw_offer.find(attrs={"class": "aditem-main--middle--description"})
        .get_text()
        .strip()
    )
    offer.price = float(
        raw_offer.find(attrs={"class": "aditem-main--middle--price-shipping--price"})
        .get_text()
        .strip()
        .split(" ")[0]
        .replace(".", "")
    )

    tag_items = raw_offer.find(attrs={"class": "aditem-main--bottom"})
    offer.key_data = []
    for tag_item in tag_items.select("span.simpletag"):
        offer.key_data.append(tag_item.get_text().strip())

    return offer
