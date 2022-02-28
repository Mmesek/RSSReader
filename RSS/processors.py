from .utils import Entry, processor, pre_processors

@processor(source="Steam", registry=pre_processors)
def steam(entry: Entry) -> bool:
    if 'A lil somethin somethin: You can find the details for this event on the announcement page' in entry.embed.description:
        return False
    return True
