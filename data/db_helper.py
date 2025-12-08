from typing import List, Dict
from models.chat_model import Chat, Conversation

class DBHelper:
    def __init__(self):
        self.chats: Dict[str, Chat] = {}    # key = chat_id, value = Chat object

    # Add a new chat session
    def create_chat(self, chat_id: str, user_name: str, user_age: int, user_gender: str):
        if chat_id in self.chats:
            raise ValueError(f"Chat ID '{chat_id}' already exists.")

        self.chats[chat_id] = Chat(
            chat_id=chat_id,
            user_name=user_name,
            user_age=user_age,
            user_gender=user_gender
        )
        return self.chats[chat_id]

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