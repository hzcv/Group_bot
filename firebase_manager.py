import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_CREDENTIAL_PATH, FIREBASE_DB_URL

cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

def get_enabled_groups():
    ref = db.reference("enabled_groups")
    return ref.get() or {}

def is_group_enabled(group_name):
    return get_enabled_groups().get(group_name, False)

def set_group_status(group_name, enabled):
    ref = db.reference(f"enabled_groups/{group_name}")
    ref.set(enabled)

def get_scheduled_messages():
    ref = db.reference("messages")
    return ref.get() or {}

def clear_message(group_name):
    db.reference(f"messages/{group_name}").delete()
