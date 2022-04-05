import json
from firebase_init import document_ref, index_ref

RECURSION_LIMIT = 128

class Transaction:
    ADD     = '$add'
    UPDATE  = '$update'
    DELETE  = '$remove'

    def __init__(self):
        self.action = None
        self.index = []
        self.value = None

    def set_action(self, action):
        self.action = action

        if action == Transaction.DELETE:
            self.value = True

    def set_value(self, value):
        self.value = value

    def push_index(self, *indices):
        for ind in indices:
            self.index.append(str(ind))

        if len(self.index) > RECURSION_LIMIT:
            raise Exception(f'Recursion depth too deep (current limit {RECURSION_LIMIT})')

    def deep_copy(self):
        t = Transaction()
        t.set_action(self.action)
        t.push_index(*self.index)
        t.set_value(self.value)
        return t

    def to_json(self):
        index_key = '.'.join(self.index)
        return {self.action: {index_key: self.value}}


class Document:
    def __init__(self, ref, transaction=None):
        self.ref = ref
        if transaction is None:
            self.transaction = Transaction()
        else:
            self.transaction = transaction

    def apply_add(self, ref, mutation, transaction):
        transaction.set_action(Transaction.ADD)
        transaction.set_value([mutation])
        index = str(len(ref.get()))
        i_id = index_ref.get()
        index_ref.set(i_id + 1)
        ref.child(index).set(mutation)
        ref.child(index).child('_id').set(i_id)
        return transaction

    def apply_delete(self, item_ref, transaction):
        item_ref.delete()
        transaction.set_action(Transaction.DELETE)
        return transaction

    def apply_update(self, item_ref, mutation, transaction):
        transactions = []
        transaction.set_action(Transaction.UPDATE)
        for key, value in mutation.items():
            if key == '_id':
                continue
            item_ref.child(str(key)).set(value)
            update_transaction = transaction.deep_copy()
            update_transaction.push_index(key)
            update_transaction.set_value(value)
            transactions.append(update_transaction)

        return transactions

    def apply_mutations(self, key, mutation_array):
        ref = self.ref.child(key)
        transactions = []

        for mutation in mutation_array:
            transaction = self.transaction.deep_copy() if self.transaction else Transaction()
            transaction.push_index(key)
            item_ref = self.get_reference_by_id(ref, mutation.get('_id'), transaction)

            if item_ref is None:
                # ADD
                transactions.append(self.apply_add(ref, mutation, transaction))
            elif '_delete' in mutation.keys():
                # DELETE
                transactions.append(self.apply_delete(item_ref, transaction))

            elif list in [type(i) for i in mutation.values()]:
                subdocument = Document(item_ref, transaction)
                subtransactions = subdocument.mutate(mutation)
                transactions.extend(subtransactions)

            else:
                # UPDATE
                transactions.extend(self.apply_update(item_ref, mutation, transaction))

        return transactions

    @staticmethod
    def get_reference_by_id(ref, _id, transaction):
        if _id is None:
            return None
        for index, item in enumerate(ref.get()):
            if item.get('_id') == _id:
                transaction.push_index(index)
                return ref.child(str(index))

    def mutate(self, mutation):
        mutations = []
        for mut_key, mut_array in mutation.items():
            if mut_key == '_id':
                continue
            mutations.extend(self.apply_mutations(mut_key, mut_array))
        return mutations

def generate_update_statement(doc_id, mutation_rawtext):
    if doc_id is None:
        raise Exception('Document _id must be provided as a query parameter')
    if not mutation_rawtext:
        raise Exception('Mutation must be provided as json in request body')
    for index, document in enumerate(document_ref.get()):
        if int(document.get('_id')) == int(doc_id):
            ref = document_ref.child(str(index))
            break
    else:
        raise Exception(f'Document _id={doc_id} does not exist')

    doc = Document(ref)
    try:
        mutation = json.loads(mutation_rawtext)
    except:
        raise Exception('Mutation must be valid json')
    return [m.to_json() for m in doc.mutate(mutation)]

