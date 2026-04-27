import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid

# Safe initialization (prevents duplicate init errors)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def log_simulation(data):
    """
    Safe, non-blocking logging function.
    Will NEVER break app flow.
    """
    try:
        print("🔥 LOGGING:", data)
        db.collection("simulation_logs").add(data)

    except Exception as e:
        # Never crash app
        print("🔥 Firebase Logging Error:", e)