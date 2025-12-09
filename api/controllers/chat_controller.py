import json
import os
import random
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from openai import OpenAI

from data.db_helper import db
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from scripts.llm_evaluation import evaluate_student_using_llm
from scripts.message_classifier import classify
from scripts.score_calculator import calculate_conversation_score

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
        model="gpt-4o-mini",
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
    # OFF-TOPIC CLASSIFICATION - PMR 02-12-25
    label = classify(message)


    if label == "off_topic":
        error_message = "This question is outside the scope of this medical training tool. Please provide a clinical question to proceed."

        db.add_message(chat_id=chat_id, message=error_message, role='bot')
        return jsonify({"response": error_message, "role":"bot"}), 200

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
def evaluate_chat(chat_id):
    if not db.chat_id_exists(chat_id):
        return jsonify({"error": "Chat not found"}), 404




    messages = db.get_chat(chat_id).conversations
    if len(messages) <2:
        return jsonify({"error": "No enough conversation to evaluate"}), 400

    # Time evaluation
    first_message_raw = db.get_chat(chat_id).conversations[0].timestamp
    last_message_raw = db.get_chat(chat_id).conversations[-1].timestamp

    # Convert to datetime
    first_message = datetime.fromisoformat(first_message_raw)
    last_message = datetime.fromisoformat(last_message_raw)

    # Now subtraction works
    duration = (last_message - first_message).total_seconds()

    # Questions Length
    total_words = 0
    for msg in messages:
        if msg.role == "doctor":
            # Split by whitespace to get words
            word_count = len(msg.message.split())
            total_words += word_count

    # Accuracy & Friendliness evaluation (LLM)
    llm_result = evaluate_student_using_llm(conversation=messages, correct_diagnosis=db.get_chat(chat_id).actual_disease)


    diagnosis_accuracy = llm_result['diagnosis_accuracy']
    conversation_friendlines = llm_result['conversation_friendliness']
    missed_questions = llm_result['missed_questions']

    final_score = calculate_conversation_score(
        duration_seconds = duration,
        total_words=total_words,
        diagnosis_accuracy= diagnosis_accuracy,
        conversation_friendliness= conversation_friendlines,
        missed_questions_count= len(missed_questions)
    )


    if messages is None:
        return jsonify({"error": "Something went wrong"}), 400
    return jsonify({
        "total_time": duration,
        "patient_name": db.get_chat(chat_id).user_name,
        "actual_disease":db.get_chat(chat_id).actual_disease,
        "ddx":db.get_chat(chat_id).ddx_list,
        "words":total_words,
        "final_score": final_score,
        "conversation_friendlines": conversation_friendlines,
        "missed_questions": missed_questions,
        "diagnosis_accuracy": diagnosis_accuracy,
    })