#!/usr/bin/env python3
from flask import Flask, request
from firebase_init import document_ref
from mutate import generate_update_statement
from reset_db import reset_db

app = Flask(__name__)

def get_documents():
    return {'documents': document_ref.get()}

@app.route('/', methods=['GET'])
def index():
    return get_documents()

@app.route('/reset', methods=['POST', 'GET'])
def reset():
    reset_db()
    return get_documents()

@app.route('/mutate', methods=['POST', 'GET'])
def mutate():
    try:
        doc_id = request.args.get('id') or request.args.get('_id')
        mutation_body = request.get_data().decode()
        return {'update_statement': generate_update_statement(doc_id, mutation_body)}
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    pass
