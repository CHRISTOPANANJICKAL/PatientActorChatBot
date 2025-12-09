from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any


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
    initial_symptom: map
    other_symptom: List[Dict[str, Any]]
    actual_disease: str
    ddx_list: List[Dict[str, Any]]
    row_index: int
    blob: str
    conversations: List[Conversation] = field(default_factory=list)