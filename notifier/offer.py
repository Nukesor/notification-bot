from datetime import datetime, timedelta

from notifier.logging import logger


class Offer:
    """
    A generic representation of an flat offer.
    """

    id: str
    link: str
    source: str

    scam: bool
    scam_reason: list[str]

    title: str
    description: str
    time: datetime | None
    raw_time: str
    key_data: list[str]

    location: str
    price: float

    def __init__(self):
        """Initialize a new raw offer object."""

        self.id = ""
        self.link = ""
        self.source = ""

        self.scam = False
        self.scam_reason = []

        self.title = ""
        self.description = ""
        self.time = None
        self.raw_time = ""
        self.key_data = []
        self.equipment = []

        self.location = ""
        self.price = 0

    def is_viable(self) -> bool:
        """Check if the current offer matches our rough criteria.

        This is mostly used to filter obviously unviable offers.
        """
        # Don't look at offers that're older than 2 hours
        threshold = datetime.now() - timedelta(days=2)
        if self.time is not None:
            if self.time < threshold:
                delta = datetime.now() - self.time
                logger.info(f"Ignoring offer (TOO OLD {delta}) for: {self.title}")
                return False

        forbidden_words = [
            "tausch",
            "mitbewohn",
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
            "allermöhe",
            "bramfeld",
            "curslack",
            "duvenstedt",
            "finkenwerder",
            "fischbek",
            "hausbruch",
            "hummelsbüttel",
            "jenfeld",
            "langenbek",
            "lohbrügge",
            "neugraben",
            "kirchwerder",
            "ochsenwerder",
            "neuengamme",
            "mamstorf",
            "meiendorf",
            "rahlstedt",
            "reitbrook",
            "rellingen",
            "rönneburg",
            "sasel",
            "sinstorf",
            "spadenland",
            "süldorf",
            "schnelsen",
            "tatenberg",
            "tonndorf",
            "volksdorf",
            # Harburg area
            "bostelbek",
            "harburg",
            "eissendorf",
            "eißendorf",
            "heimfeld",
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

    def clean(self):
        """Clean the offer from unwanted markdown symbols."""
        markdown_characters = ["[", "`", "*", "_", "`"]
        translation_table = dict.fromkeys(map(ord, "".join(markdown_characters)), None)

        self.title = self.title.translate(translation_table)
        self.description = self.description.translate(translation_table)

    def format(self) -> str:
        """Bring the offer into human readable format."""
        # Clean the offer from unwanted symbols
        self.clean()

        # Show a scam text, if the offer is a scam
        if self.scam:
            reasons = ", ".join(self.scam_reason)
            text = f"""
[SCAM: {self.title}]({self.link})
Gründe: {reasons}
"""
            return text

        if self.time is None:
            formatted_time = str(self.raw_time)
        else:
            formatted_time = self.time.strftime("%m.%d.%y - %H:%M")

        # Only show equipment, if it exists.
        equipment = ""
        if len(self.equipment) != 0:
            equipment = "\n" + ", ".join(self.equipment)

        description = ""
        if self.description != "":
            description = f"\n---\n{self.description}\n"

        key_data = ", ".join(self.key_data)
        text = f"""Von {self.source}:
[{self.title}]({self.link})

{self.location}

{self.price:.0f} €, {key_data}
{equipment} {description}
Gepostet: {formatted_time}
"""

        return text

    def __repr__(self) -> str:
        return self.format()
