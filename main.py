from dotenv import load_dotenv

from api import create_app
from data.db_helper import db
from scripts.message_classifier import load_classifier

db.load_cases_from_json()
load_dotenv()
load_classifier()

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

