import os
from datetime import datetime
import uuid

# ──────────────────────────────────────────────
# Safe Firebase initialisation
# Works when firebase_admin is installed AND firebase_key.json exists.
# Degrades gracefully to a no-op logger on Render / environments
# where either is missing.
# ──────────────────────────────────────────────

_firebase_ready = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    _key_path = os.path.join(os.path.dirname(__file__), "..", "firebase_key.json")
    if os.path.exists(_key_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(_key_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        _firebase_ready = True
    else:
        db = None
        print("⚠️ firebase_key.json not found — Firebase logging disabled.")
except ImportError:
    db = None
    print("⚠️ firebase_admin not installed — Firebase logging disabled.")
except Exception as e:
    db = None
    print(f"⚠️ Firebase init failed: {e} — Firebase logging disabled.")


def log_simulation(data):
    """
    Safe, non-blocking logging function.
    Will NEVER break app flow.
    """
    try:
        print("🔥 LOGGING:", data)
        if _firebase_ready and db is not None:
            db.collection("simulation_logs").add(data)
        else:
            print("ℹ️ Firebase unavailable — log written to console only.")
    except Exception as e:
        # Never crash app
        print("🔥 Firebase Logging Error:", e)