from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from RSS.models import Feed_Post
    from RSS.webhooks.models import Subscription

LIMITS: dict[str, "Limits"] = {}
REQUESTS: dict[str, "Request"] = {}


class Limits:
    TOTAL = None
    EMBEDS = None

    def __init_subclass__(cls) -> None:
        LIMITS[cls.__name__.lower()] = cls


class Serializer:
    def as_dict(self):
        json = {}
        for attribute in self.__annotations__:
            if attribute in self.__dict__:
                json[attribute] = self.__dict__[attribute]
        return json


class Request(Serializer):
    def __init__(self, sub: "Subscription", entries: list["Feed_Post"]) -> None:
        raise NotImplementedError

    def __init_subclass__(cls) -> None:
        REQUESTS[cls.__name__.lower()] = cls
