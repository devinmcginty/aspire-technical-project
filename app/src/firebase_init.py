import os
import sys
import firebase_admin
from firebase_admin import db, credentials

if 'pytest' in sys.modules:
    document_ref = None
    index_ref = None
else:
    private_key_json = os.environ.get('FIREBASE_JSON_KEY')
    db_identifier = os.environ.get('FIREBASE_DB_IDENTIFIER')

    if not private_key_json:
        raise Exception('Set the private key file path with env var FIREBASE_JSON_KEY')
    if not db_identifier:
        raise Exception('Set the Firebase database identifier with env var FIREBASE_DB_IDENTIFIER')

    auth = credentials.Certificate(private_key_json)
    firebase_admin.initialize_app(auth, {
        'databaseURL': f"https://{db_identifier}.firebaseio.com/",
    })
    db_ref = db.reference('/')

    document_ref = db_ref.child('documents')
    index_ref = db_ref.child('index')
