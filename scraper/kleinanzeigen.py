from bs4 import BeautifulSoup
import os
import time
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
import requests
import traceback
from datetime import datetime, timedelta
import pprint


from scraper.config import config

known_ids_path = os.path.expanduser("~/.local/share/kleinanzeigen_known_ids")

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "www.kleinanzeigen.de",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}


# This is super hacky.
# For now, we just save all known offers in global state list.
# We'll forget which offers we already inspected the second the bot is restarted.
known_ids = []


async def scrape(context: CallbackContext) -> None:
    try:
        await scrape_inner(context)
    except Exception as ex:
        print(f"Got exception {ex}")
        traceback.print_exc()
        # await context.bot.sendMessage(
        #    chat_id=config["telegram"]["target_channel"],
        #    text=f"Scraper failed with exception {ex}",
        # )
        return


async def scrape_inner(context: CallbackContext) -> None:
    """Scrape Kleinanzeigen and send regular updates on new events."""

    # Load the side with the correct offers
    url = "https://www.kleinanzeigen.de/s-wohnung-mieten/hamburg/anzeige:angebote/c203l9409+wohnung_mieten.qm_d:65%2C200+wohnung_mieten.zimmer_d:3%2C5"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Got response with status code {response.status_code}")

    # Get the list of all ids that we already sent
    known_ids = []
    if os.path.exists(known_ids_path):
        with open(known_ids_path, "r") as reader:
            text = reader.read().strip()
            known_ids = text.split("\n")

    soup = BeautifulSoup(response.text, "html.parser")
    # soup.prettify()

    container = soup.select("div.l-container-row.contentbox-unpadded.no-bg")[0]
    if container is None:
        print("Failed to get container. Please investigate.")
        return

    offer_list = container.find("ul")

    if offer_list is None:
        return

    offer_details = []
    for offer in offer_list.find_all("li"):
        try:
            details = get_offer_details(offer)

            # There're some list items that aren't offers
            if details is None:
                continue

            offer_details.append(details)
        except Exception as ex:
            print(f"Got exception {ex} for the following block:")
            print(offer.prettify())

            raise ex

    for offer in offer_details:
        # Don't send infos twice
        if offer["id"] in known_ids:
            continue

        # Don't look at offers that're older than 2 hours
        threshold = datetime.now() - timedelta(hours=2)
        if offer["time"] is not None:
            if offer["time"] < threshold:
                continue

        await context.bot.sendMessage(
            chat_id=config["telegram"]["target_channel"],
            text=format_offer(offer),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

        time.sleep(2)

        known_ids.append(offer["id"])

    # Write the known_ids file back to disk
    with open(known_ids_path, "w") as descriptor:
        descriptor.write("\n".join(known_ids))


def format_offer(offer):
    if offer["time"] is None:
        formatted_time = offer["time"]
    else:
        formatted_time = offer["time"].strftime("%m.%d - %H:%M")

    link = "https://kleinanzeigen.de" + offer["link"]
    tags = ", ".join(offer["tags"])
    text = f"""
*Title:* {offer["header"]}
*link:* [Angebot]({link})
*Date:*  {offer["raw_time"]} ({formatted_time})
*Price:* {offer["price"]}
*Tags:*  {tags}

---

{offer["description"]}
"""

    return text


def get_offer_details(offer):
    details = {}

    # Filter list items that aren't offers
    if offer.find("article") is None:
        return None

    details["link"] = offer.find("article").attrs["data-href"]
    # The id of the offer is the very last item of the link
    details["id"] = details["link"].split("/")[-1]
    details["area"] = (
        offer.find(attrs={"class": "aditem-main--top--left"}).get_text().strip()
    )

    # Determine the date this offer has been created at.
    time = offer.find(attrs={"class": "aditem-main--top--right"}).get_text().strip()
    details["raw_time"] = time
    if time == "":
        details["time"] = None
    else:
        # Parse the offer time, which is formatted like this:
        # Gestern, 18:01
        # Heute, 12:15
        split = time.split(", ")

        # Get the date part and split the time into hour + minute
        day = split[0]
        time = split[1].split(":")

        # Set the date based on the date string
        offer_date = datetime.now()
        if day == "Gestern":
            offer_date = offer_date - timedelta(days=1)

        # Set the time
        offer_date.replace(
            hour=int(time[0]), minute=int(time[1]), second=0, microsecond=0
        )

        details["time"] = offer_date

    main_content = offer.find(attrs={"class": "aditem-main--middle"})
    details["header"] = main_content.find("h2").get_text().strip()
    details["description"] = (
        offer.find(attrs={"class": "aditem-main--middle--description"})
        .get_text()
        .strip()
    )
    details["price"] = (
        offer.find(attrs={"class": "aditem-main--middle--price-shipping--price"})
        .get_text()
        .strip()
    )

    tag_items = offer.find(attrs={"class": "aditem-main--bottom"})
    details["tags"] = []
    for tag_item in tag_items.select("span.simpletag"):
        details["tags"].append(tag_item.get_text().strip())

    return details
