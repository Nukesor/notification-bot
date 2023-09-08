import os
import tomllib

import tomli_w

known_ids_path = os.path.expanduser("~/.local/share/notifier_known_ids.toml")


class KnownKeys:
    """Handles already notified items.

    This class holds all keys for things that the bot already notified about.
    It handles the keys of each site individually.
    """

    known_keys: dict[str, list[str]] = {}

    def __init__(self) -> None:
        self.known_keys = {}

    def has_key(self, site: str, key: str) -> bool:
        """Check if a key has been notified about for a particular site."""
        if site not in self.known_keys:
            return False

        return key in self.known_keys[site]

    def add_key(self, site: str, key: str):
        """Save a notified key to a site."""
        if site not in self.known_keys:
            self.known_keys[site] = []

        if not self.has_key(site, key):
            self.known_keys[site].append(key)

    def read_from_disk(self):
        """Read the known list from disk."""
        # Don't read if there's no file yet.
        if not os.path.exists(known_ids_path):
            return

        with open(known_ids_path, "rb") as file_descriptor:
            self.known_keys = tomllib.load(file_descriptor)

    def write_to_disk(self):
        """Write the current updated list to disk."""
        with open(known_ids_path, "wb") as file_descriptor:
            tomli_w.dump(self.known_keys, file_descriptor)
