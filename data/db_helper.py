from typing import List, Dict
from datetime import datetime
from models.chat_model import Chat, Conversation
import json
import os


class DBHelper:
    def __init__(self):
        self.chats: Dict[str, Chat] = {}    # key = chat_id, value = Chat object
        self.cases_json: List = []


    # Load the cases from the json
    def load_cases_from_json(self):
        if self.cases_json not in (None, []) and self.cases_json != {}:
            return self.cases_json

        # path = "data/processed/cases_part_00001.json"
        path = "data/processed/sample.json"
        if not os.path.exists(path):
            raise FileNotFoundError(f"JSON file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self.cases_json = json.load(f)

            return self.cases_json

    # Add a new chat session
    def create_chat(self, chat_id: str, user_name: str, user_age: int, user_gender: str,
                    initial_symptom: map,
                    actual_disease: str,
                    ddx_list: List,
                    row_index: int,
                    blob : str,
                    other_symptom: List
                    ):
        if chat_id in self.chats:
            raise ValueError(f"Chat ID '{chat_id}' already exists.")

        self.chats[chat_id] = Chat(
            chat_id=chat_id,
            user_name=user_name,
            user_age=user_age,
            user_gender=user_gender,
            initial_symptom=initial_symptom,
            other_symptom=other_symptom,
            actual_disease = actual_disease,
            row_index = row_index,
            blob = blob,
            ddx_list = ddx_list
        )
        return chat_id

    # Add a conversation/message to a specific chat
    def add_message(self, chat_id: str, role: str, message: str, **kwargs):
        if chat_id not in self.chats:
            raise ValueError(f"Chat ID '{chat_id}' not found.")

        conv = Conversation(role=role, message=message)
        self.chats[chat_id].conversations.append(conv)
        return conv

    # Retrieve a specific chat by its ID
    def get_chat(self, chat_id: str) -> Chat:
        if chat_id not in self.chats:
            raise ValueError(f"Chat ID '{chat_id}' does not exist.")
        print(self.chats)

        return self.chats[chat_id]



    # List all chats (just metadata, not messages)
    def list_chats(self) -> List[Dict]:
        return [
            {
                "chat_id": chat.chat_id,
                "user_name": chat.user_name,
                "user_age": chat.user_age,
                "user_gender": chat.user_gender,
                "conversation_count": len(chat.conversations)
            }
            for chat in self.chats.values()
        ]

    def delete_chat(self, chat_id: str):
        self.chats.pop(chat_id, None)


    def chat_id_exists(self, chat_id: str) -> bool:
        return chat_id in self.chats


db = DBHelper()