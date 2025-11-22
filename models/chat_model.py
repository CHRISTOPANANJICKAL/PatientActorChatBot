from datetime import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass
class Conversation:
    role: str          # "doctor" or "bot"
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Chat:
    chat_id: str
    user_name: str
    user_age: int
    user_gender: str
    conversations: List[Conversation] = field(default_factory=list)