from .utils import Entry, processor

@processor
def blacklist(entry: Entry, value: str) -> bool:
    if value in entry.embed.description:
        return False
    return True
