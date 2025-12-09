import json
import os

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def evaluate_student_using_llm(conversation, correct_diagnosis, ):
    conversation_text = ""
    for msg in conversation:
        conversation_text += f"{msg.role.capitalize()}: {msg.message}\n"

    # Prepare prompt
    system_prompt = """
You are a senior medical evaluator. 
You will receive:
1. A full conversation between a medical student (doctor) and a patient.
2. The correct diagnosis.
3. Find the student diagnosis from conversation.
4. The original patient case.

You must evaluate the student on:
- Diagnosis accuracy (if not found grade accordingly) (0–10)
- Friendliness & communication quality (0–10)
- Missed important questions (list of strings)

Return ONLY a JSON in this exact format:

{
  "diagnosis_accuracy": 0-10 integer,
  "conversation_friendliness": 0-10 integer,
  "missed_questions": ["q1", "q2"]
}

Do NOT add explanations.
    """

    # Build user message
    user_prompt = f"""
Conversation:
{conversation_text}

Correct diagnosis: {correct_diagnosis}

Go through the conversation and if you find the correct diagnosis in the chat, give the credits accordingly.
Now evaluate and return the JSON only.
    """


    print(user_prompt)
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            ChatCompletionSystemMessageParam(role="system", content= system_prompt),
            ChatCompletionUserMessageParam(role="user", content= user_prompt)
        ],
        temperature=0.4,
    )


    # Extract and parse JSON from the model's output
    try:
        result = json.loads(response.choices[0].message.content)
        print(result)
    except:
        # fallback if model adds extra text
        cleaned = response.choices[0].message.content.strip()
        cleaned = cleaned[cleaned.find("{"): cleaned.rfind("}")+1]
        result = json.loads(cleaned)
        print("exception result")
        print(result)

    return result