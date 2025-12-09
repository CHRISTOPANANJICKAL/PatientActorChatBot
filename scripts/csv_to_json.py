from flask import jsonify

evidences_map = {}
df = []

def convert_csv_to_json():

    import pandas as pd
    import json
    import os

    global evidences_map, df

    # ---------------------------
    # Load evidences_map
    # ---------------------------
    if not evidences_map:
        with open("data/raw/release_evidences.json", "r") as f:
            evidences_map = json.load(f)

    # ---------------------------
    # Load CSV
    # ---------------------------
    if len(df) == 0:
        csv_path = "data/raw/train.csv"

        if not os.path.exists(csv_path):
            return jsonify({"error": "CSV file not found"}), 500

        df = pd.read_csv(csv_path)

    total_rows = len(df)
    print(f"Starting export: {total_rows} rows found")

    # ---------------------------
    # Prepare output folder
    # ---------------------------
    output_folder = "data/output/cases"
    os.makedirs(output_folder, exist_ok=True)

    # chunk size (adjust if needed)
    chunk_limit = 100000

    file_index = 1
    batch = []
    processed = 0

    # ---------------------------
    # Loop through dataframe
    # ---------------------------
    for i, row in df.iterrows():

        # Log progress
        if i % 10000 == 0:
            print(f"Processing row {i}/{total_rows}")

        try:
            description = describe_patient_row(row)
        except Exception as e:
            print(f"❌ Error at row {i}: {e}")
            continue  # skip broken rows

        batch.append({
            "row_index": int(i),
            "patient": description
        })

        processed += 1

        # ---------------------------
        # Save chunk to file
        # ---------------------------
        if len(batch) >= chunk_limit:

            file_path = os.path.join(
                output_folder,
                f"cases_part_{file_index:05d}.json"
            )

            with open(file_path, "w") as f:
                json.dump(batch, f, indent=2)

            print(f"✔ Saved chunk {file_index} ({len(batch)} records) → {file_path}")

            file_index += 1
            batch = []   # clear memory

    # ---------------------------
    # Save remaining rows
    # ---------------------------
    if batch:
        file_path = os.path.join(
            output_folder,
            f"cases_part_{file_index:05d}.json"
        )
        with open(file_path, "w") as f:
            json.dump(batch, f, indent=2)

        print(f"✔ Saved final chunk ({len(batch)} records) → {file_path}")

    # ---------------------------
    # API response
    # ---------------------------
    return jsonify({
        "status": "ok",
        "exported": processed,
        "chunks_created": file_index,
        "output_folder": output_folder
    }), 200


import ast
def describe_patient_row(row):

    age = int(row["AGE"])
    gender = str(row["SEX"])
    actual_disease = str(row["PATHOLOGY"])


    initial_symptom = str(row["INITIAL_EVIDENCE"])



    ans, question = get_evidence_str(initial_symptom)
    initial_evidence_map_cleaned = {
        "question":question,
        "answer":ans,
    }

    evidence_list = ast.literal_eval(str(row["EVIDENCES"]))

    other_symptoms_cleaned = []

    for evidence_code in evidence_list:
        ans, question = get_evidence_str(evidence_code)

        cleaned = {
              "question":question,
               "answer":ans,
        }

        other_symptoms_cleaned.append(cleaned)


    ddx_raw = row["DIFFERENTIAL_DIAGNOSIS"]
    ddx = ast.literal_eval(ddx_raw)

    ddx_list = []
    for disease, prob in ddx:
        percentage = int(round(float(prob) * 100))
        ddx_list.append({
            "symptom": str(disease),
            "probability": percentage
        })

    from faker import Faker

    fake = Faker()

    def random_name_by_gender(gender):
        if gender.upper() == "M":
            return fake.name_male()
        elif gender.upper() == "F":
            return fake.name_female()
        else:
            return fake.name()

    return {
        "name": random_name_by_gender(gender),
        "age": age,
        "gender": gender,
        "actual_disease": actual_disease,
        "initial_symptom": initial_evidence_map_cleaned,
        "other_symptom": other_symptoms_cleaned,
        "ddx_list": ddx_list,
    }


def get_evidence_str(code_in):
    import random

    # -----------------------------
    # 1. Split code and forced value
    # -----------------------------
    forced_value = None

    if "_@_" in code_in:
        parts = code_in.split("_@_")
        code = parts[0]
        forced_value = parts[1]
    else:
        code = code_in

    # -----------------------------
    # 2. Look up evidence definition
    # -----------------------------
    if code not in evidences_map:
        print(f"[WARNING] Unknown evidence code: {code}")
        return "Unknown", "Unknown question"

    info = evidences_map[code]

    question = info.get("question_en", "Unknown question")
    default_value = info.get("default_value")
    data_type = info.get("data_type")
    value_meaning = info.get("value_meaning", {})

    # -----------------------------
    # 3. Apply forced value override
    # -----------------------------
    if forced_value is not None:
        chosen_value = forced_value
    else:
        chosen_value = default_value

    # -----------------------------
    # 4. Convert to readable text
    # -----------------------------
    level_text = None

    # Boolean → random Yes/No
    if data_type == "B":
        level_text = random.choice(["Yes", "No"])

    # Category type (C)
    elif data_type == "C":
        # pick random possible value if available
        if value_meaning:
            chosen_value = random.choice(list(value_meaning.keys()))

        meaning = value_meaning.get(chosen_value, chosen_value)

        if isinstance(meaning, dict):
            level_text = meaning.get("en", chosen_value)
        else:
            level_text = meaning

    # Multi-choice (M)
    elif data_type == "M":
        # pick random possible value if available
        if value_meaning:
            chosen_value = random.choice(list(value_meaning.keys()))

        meaning = value_meaning.get(chosen_value, chosen_value)

        if isinstance(meaning, dict):
            level_text = meaning.get("en", chosen_value)
        else:
            level_text = meaning

    # Fallback
    if level_text is None:
        level_text = str(chosen_value)

    try:
        num = float(level_text)
        level_text =  f"{num}/10"
    except (ValueError, TypeError):
        level_text = level_text

    return level_text, question


