import uuid

from flask import Blueprint, request, jsonify
from data.db_helper import DBHelper

chat_bp = Blueprint("chat", __name__)


db = DBHelper()

@chat_bp.route("/start_chat", methods=["POST"])
def start_chat():
    new_chat_id = str(uuid.uuid4())
    chat_id = db.create_chat(chat_id=new_chat_id, user_name=request.json.get("user_name"),
                                      user_age=request.json.get("user_age"),
                                     user_gender=request.json.get("user_gender")
                                     )


    return jsonify({"chat_id": chat_id, "message": "New chat started!"})

@chat_bp.route("/chats", methods=["GET"])
def list_chats():
    return jsonify(db.list_chats())

@chat_bp.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    chat_id = data.get("chat_id")
    message = data.get("message")

    db.add_message(chat_id=chat_id, message=message, role='doctor')
    response = "glad to meet you doctor"
    db.add_message(chat_id=chat_id, message=response, role='bot')

    return jsonify({"response": response, "role":"bot"})


@chat_bp.route("/get_messages/<chat_id>", methods=["GET"])
def get_messages(chat_id):
    if not db.chat_id_exists(chat_id):
        return jsonify({"message": "Chat not found"}), 404

    messages = db.get_chat(chat_id)
    if messages is None:
        return jsonify({"error": "No message to add"}), 400
    return jsonify({"chat_id": chat_id, "messages": messages})