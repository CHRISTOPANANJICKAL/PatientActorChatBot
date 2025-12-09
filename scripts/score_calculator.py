def calculate_conversation_score(
    duration_seconds,
    total_words,
    diagnosis_accuracy,
    conversation_friendliness,
    missed_questions_count
):
    """
    Calculates a final score between 0 and 10 based on conversation metrics.
    """

    # -------------------------
    # 1. Normalize duration (shorter = better)
    # -------------------------
    # Define upper limit (anything above this gets 0)
    MAX_DURATION = 1200  # 20 minutes

    duration_score = max(0, 1 - (duration_seconds / MAX_DURATION))
    duration_score *= 10  # convert to 0–10


    # -------------------------
    # 2. Normalize word count (fewer = better)
    # -------------------------
    MAX_WORDS = 1000  # anything above this = 0 score

    word_score = max(0, 1 - (total_words / MAX_WORDS))
    word_score *= 10


    # -------------------------
    # 3. Diagnosis accuracy (already out of 10)
    # -------------------------
    diagnosis_score = diagnosis_accuracy  # 0–10


    # -------------------------
    # 4. Conversation friendliness (already 0–10)
    # -------------------------
    friendliness_score = conversation_friendliness


    # -------------------------
    # 5. Missed questions (fewer = better)
    # -------------------------
    MAX_MISSED = 3

    missed_score = max(0, 1 - (missed_questions_count / MAX_MISSED))
    missed_score *= 10


    # -------------------------
    # FINAL WEIGHTS
    # -------------------------
    WEIGHTS = {
        "duration": 0.15,
        "words": 0.15,
        "diagnosis": 0.30,
        "friendliness": 0.25,
        "missed": 0.15,
    }

    final_score = (
        duration_score * WEIGHTS["duration"] +
        word_score * WEIGHTS["words"] +
        diagnosis_score * WEIGHTS["diagnosis"] +
        friendliness_score * WEIGHTS["friendliness"] +
        missed_score * WEIGHTS["missed"]
    )

    return round(final_score, 2)