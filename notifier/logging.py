import logging

# Enable logging
logging.basicConfig(
    # Add %(name)s if there're some undesired logs.
    # This shows the name of the library you most likely want to hide
    format="%(asctime)s %(levelname)s:  %(message)s",
    level=logging.INFO,
)


logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
