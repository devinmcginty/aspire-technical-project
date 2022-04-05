from firebase_init import document_ref, index_ref

doc = {
    "_id": 1,
    "name": "Johnny Content Creator",
    "posts": [
        {
            "_id": 2,
            "value": "one",
            "mentions": []
        },
        {
            "_id": 3,
            "value": "two",
            "mentions": [
                {
                    "_id": 5,
                    "text": "apple"
                },
                {
                    "_id": 6,
                    "text": "orange"
                }
            ]
        },
        {
            "_id": 4,
            "value": "three",
            "mentions": []
        }
    ]
}

def reset_db():
    document_ref.child('0').set(doc)
    index_ref.set(7)

