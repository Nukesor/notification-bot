from datetime import datetime, timedelta

from notifier.logging import logger


class Offer:
    """
    A generic representation of an flat offer.
    """

    id: str
    link: str

    title: str
    description: str
    time: datetime | None
    raw_time: str
    tags: list[str]

    location: str
    price: int

    def __init__(self):
        """Initialize a new raw offer object."""

        self.id = ""
        self.link = ""
        self.title = ""

        self.description = ""
        self.time = None
        self.raw_time = ""
        self.tags = []

        self.location = ""
        self.price = 0

    def is_viable(self) -> bool:
        """Check if the current offer matches our rough criteria.

        This is mostly used to filter obviously unviable offers.
        """
        # Don't look at offers that're older than 2 hours
        threshold = datetime.now() - timedelta(hours=2)
        if self.time is not None:
            if self.time < threshold:
                delta = datetime.now() - self.time
                logger.info(f"Ignoring offer (TOO OLD {delta}) for: {self.title}")
                return False

        forbidden_words = [
            "untermiete",
            "zwischenmiete",
            "möbliert",
        ]

        # Filter offers that contain forbidden words in their title or description
        for area in forbidden_words:
            if area in self.title.lower() or area in self.description.lower():
                logger.info(f"Ignoring offer (FORBIDDEN WORD) for: {self.title}")
                return False

        forbidden_areas = [
            "altengamme",
            "bramfeld",
            "finkenwerder",
            "hausbruch",
            "lohbrügge",
            "rahlstedt",
            "sasel",
            "schnelsen",
            "tonndorf",
        ]
        # Filter areas that're unsuitable for us
        for area in forbidden_areas:
            if (
                area in self.title.lower()
                or area in self.description.lower()
                or area in self.location.lower()
            ):
                logger.info(f"Ignoring offer (FORBIDDEN AREA) for: {self.title}")
                return False

        return True

    def format(self) -> str:
        if self.time is None:
            formatted_time = str(self.time)
        else:
            formatted_time = self.time.strftime("%m.%d - %H:%M")

        tags = ", ".join(self.tags)
        text = f"""
*Title:* {self.title}
*Gegend:* {self.location}
*Link:* [Angebot]({self.link})
*Date:*  {self.raw_time} ({formatted_time})
*Price:* {self.price}
*Tags:*  {tags}

---

{self.description}
"""

        return text
