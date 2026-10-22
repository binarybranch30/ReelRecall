from abc import ABC, abstractmethod
from datetime import datetime

from reelsaver.models import Share, TextMessage


class ShareSource(ABC):

    @abstractmethod
    def get_new_messages(self, since: datetime | None = None) -> tuple[list[Share], list[TextMessage]]:
        ...
        
    def get_new_shares(self, since: datetime | None = None) -> list[Share]:
        return self.get_new_messages(since)[0]