import os
import joblib
import logging



# CLASSIFIER_THRESHOLD = float(os.getenv("CLASSIFIER_THRESHOLD", 0.5))
CLASSIFIER_MODEL_VERSION = os.getenv("CLASSIFIER_MODEL_VERSION", "1.0.0")


# =====================================================================================
# Setup logging
# =====================================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# =====================================================================================
# Load the classifier model
# =====================================================================================
MODEL_PATH = os.path.join("ml_models", "message_classifier.pkl")

svc_model = None

def load_classifier():
    try:
        global svc_model
        svc_model = joblib.load(MODEL_PATH)
        logger.info(f"[MessageClassifier] Model loaded from {MODEL_PATH}")
    except Exception as e:
        logger.error(f"[MessageClassifier] Failed to load model: {e}")
        svc_model = None  # fallback: safe degradation


# =====================================================================================
# Utility: clean input text
# =====================================================================================
def _normalize_text(text):
    # Convert None → ""
    if text is None:
        return ""

    # Force string
    text = str(text).strip()

    # Hard limit to avoid strange payloads
    if len(text) > 1000:
        text = text[:1000]

    return text


# =====================================================================================
# Public function: classify message
# =====================================================================================
def classify(text: str) -> str:
    """
    Classify a message as 'on_topic' or 'off_topic' using the trained pipeline.
    Safe and production-ready.

    Returns:
        str: "on_topic" or "off_topic"
    """
    global svc_model
    CLASSIFIER_THRESHOLD = -0.5


    logger.info(f"[Classifier v{CLASSIFIER_MODEL_VERSION}] Running inference…")

    # Normalize input
    message = _normalize_text(text)

    # If empty → treat as off-topic
    if not message:
        logger.warning("[MessageClassifier] Empty message detected → off_topic")
        print('off_topic because message is empty')
        return "off_topic"

    # If model failed to load, fail gracefully
    if svc_model is None:
        logger.warning("[MessageClassifier] Model unavailable → default to on_topic")
        print("on_topic = model unavailable")
        return "on_topic"


    try:
        # ------------------------------
        # 1. Compute decision score (confidence proxy)
        # ------------------------------
        score = svc_model.decision_function([message])[0]
        logger.info(f"[MessageClassifier] decision_function score={score:.4f} threshold={CLASSIFIER_THRESHOLD}")

        # ------------------------------
        # 2. Apply REAL threshold
        # ------------------------------
        # if score < CLASSIFIER_THRESHOLD:
        print(f'score={score:.4f} threshold={CLASSIFIER_THRESHOLD} {score < CLASSIFIER_THRESHOLD}')
        if score < CLASSIFIER_THRESHOLD:
            print(f'Off-topic, because score less then threshold')
            logger.info("[MessageClassifier] Below threshold → off_topic")
            return "off_topic"
        return 'on_topic'

        # # ------------------------------
        # # 3. Predict using model
        # # ------------------------------
        # prediction = svc_model.predict([message])[0]
        # logger.info(f"[MessageClassifier] Model prediction → {prediction}")
        # print(f'prediction={prediction}')

    except Exception as e:
        logger.error(f"[MessageClassifier] Prediction error: {e}")
        print(f'on topic due to exception: {e}')
        return "on_topic"  # safest fallback


# =====================================================================================
# Quick manual test (optional)
# =====================================================================================
if __name__ == "__main__":
    tests = [
        "hello bro",
        "I have been vomiting",
        "why are you asking me this?",
        "I feel chest pain when breathing",
        ""
    ]

    for t in tests:
        print(t, "→", classify(t))
