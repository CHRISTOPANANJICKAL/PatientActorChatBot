import json
import os
import random
import uuid

from flask import Blueprint, request, jsonify
from openai import OpenAI
from datetime import  datetime

from data.db_helper import db
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

chat_bp = Blueprint("chat", __name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@chat_bp.route("/start_chat", methods=["GET"])
def start_chat():
    new_chat_id = str(uuid.uuid4())

    index = random.randint(0, len(db.cases_json) - 1)
    current_case = db.cases_json[index]


    print(current_case)
    row_index = current_case["row_index"]
    name = current_case["patient"]["name"]
    age = current_case["patient"]["age"]
    gender = current_case["patient"]["gender"]
    actual_disease = current_case["patient"]["actual_disease"]
    initial_symptom = current_case["patient"]["initial_symptom"]
    other_symptom = current_case["patient"]["other_symptom"]
    ddx_list = current_case["patient"]["ddx_list"]

    combined_json_text = (
            "Name:" + name + "Age:" + str(age)  +
            "Initial Symptom:"+
            json.dumps(initial_symptom, indent=2) +
            "Other Symptoms:" +
            json.dumps(other_symptom, indent=2)
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or gpt-4 if available
        messages=[
            ChatCompletionUserMessageParam(role="user", content=(
        "You are a patient. Some details of disease you have is given to you. "
        "You have to generate a text blob describing your symptoms. Be really descriptive."
        "Here are the details:\n\n"
        + combined_json_text))
        ],
            temperature=0.4,
            max_tokens=3000
    )

    final_response = response.choices[0].message.content


    chat_id = db.create_chat(chat_id=new_chat_id,
                             user_name=name,
                             user_age=age,
                             user_gender=gender,
                             other_symptom=other_symptom,
                             initial_symptom=initial_symptom,
                             actual_disease =actual_disease,
                             ddx_list=ddx_list,
                             row_index=row_index,
                             blob =final_response
                             )


    return jsonify({"chat_id": chat_id, "message": "New chat started!"})

@chat_bp.route("/chats", methods=["GET"])
def list_chats():
    return jsonify(db.list_chats())

@chat_bp.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    chat_id = data.get("chat_id")
    if not db.chat_id_exists(chat_id):
        return jsonify({"message": "Chat not found"}), 404


    message = data.get("message")
    text_blob = db.get_chat(chat_id).blob
    db.add_message(chat_id=chat_id, message=message, role='doctor')
    old_message = []
    # add conversation history
    for c in db.get_chat(chat_id).conversations:
        if c.role == "doctor":
            role = "user"
        else:
            role = "system"

        old_message.append(
            ChatCompletionUserMessageParam(role=role, content=c.message)
            if role == "user" else
            ChatCompletionSystemMessageParam(role="system", content=c.message)
        )

    messages = [
        ChatCompletionSystemMessageParam(role="system",
                                            content="I am a patient who is consulting a doctor(user).Always remember the AI is the patient and the doctor is going to ask the questions to you. Give answers one by one. Not all at once. Here is what you have." + text_blob + "Give proper answers from this one by one as the doctor asks. If something is out of context (anything not released to your health condition) of given data just say im not sure, ask me something else"
                                            ),
    ]

    messages.extend(old_message)
    messages.append(ChatCompletionUserMessageParam(role="user", content=message))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
       messages=messages,
        temperature=0.4,
        max_tokens=3000
    )
    final_response = response.choices[0].message.content

    db.add_message(chat_id=chat_id, message=final_response, role='bot')

    return jsonify({"response": final_response, "role":"bot"})


@chat_bp.route("/get_messages/<chat_id>", methods=["GET"])
def get_messages(chat_id):
    if not db.chat_id_exists(chat_id):
        return jsonify({"message": "Chat not found"}), 404

    messages = db.get_chat(chat_id)
    if messages is None:
        return jsonify({"error": "No message to add"}), 400
    return jsonify(messages)


@chat_bp.route("/delete_messages", methods=["POST"])
def delete_messages():
    data = request.get_json()

    # Validate input
    if not data or "chat_ids" not in data or not isinstance(data["chat_ids"], list):
        return jsonify({"error": "chat_ids must be provided as a list"}), 400

    chat_ids = data["chat_ids"]

    deleted = []
    not_found = []

    for cid in chat_ids:
        if db.chat_id_exists(cid):
            db.delete_chat(cid)
            deleted.append(cid)
        else:
            not_found.append(cid)

    return jsonify({
        "status": "completed",
        "deleted": deleted,
        "not_found": not_found
    }), 200


@chat_bp.route("/evaluate/<chat_id>", methods=["GET"])
def get_messages(chat_id):
    if not db.chat_id_exists(chat_id):
        return jsonify({"message": "Chat not found"}), 404

    messages = db.get_chat(chat_id)
    if messages is None:
        return jsonify({"error": "No message to add"}), 400
    return jsonify(messages)