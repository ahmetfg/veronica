import firebase_admin as fb
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.services.firestore.client import FirestoreClient

# init GCP
def initialize():
    # init firebase admin
    cred = credentials.Certificate("veronica/GCP_CRIDENTIALS.json")
    fb.initialize_app(cred)
    db : FirestoreClient = firestore.client()

    return db

# reset bot database
def set_database(db):
    try:
        null_bot_Data = {
                    '0': [True, None, None],
                    '1': [None, None, None],
                    '2': [None, None, None],
                    '3': [None, None, None],
                    '4': [None, None, None],
                    '5': [None, None, None],
                    '6': [None, None, None],
                    '7': [None, None, None]
        }
        db.collection('datas').document('receptorData').set(null_bot_Data)
        print("bot database reset succesfully")
    except:
        print("bot database reset failed")

# fetch data from bot database
def get_database(db):
    try:
        data = db.collection('datas').document('receptorData').get().to_dict()
        print(data)
    except:
        print("bot database fetch failed")