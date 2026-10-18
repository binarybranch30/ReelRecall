from abc import ABC, abstractmethod
from datetime import datetime

from reelsaver.models import Share


class ShareSource(ABC):

    @abstractmethod
    def get_new_shares(self, since: datetime | None = None) -> list[Share]:
        ...   