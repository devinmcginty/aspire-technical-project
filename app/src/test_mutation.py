from unittest.mock import patch, MagicMock

import pytest
from mutate import generate_update_statement, Document

class TestGenerateUpdateStatement:
    doc_id = 1
    mutation_text = '{"posts": [{"foo": "bar"}]}'

    def test_requires_document_id(self):
        with pytest.raises(Exception) as context:
            generate_update_statement(None, self.mutation_text)
        assert "Document _id" in str(context.value)

    def test_requires_mutation(self):
        with pytest.raises(Exception) as context:
            generate_update_statement(self.doc_id, '')
        assert "Mutation must be" in str(context.value)

    @patch('mutate.document_ref')
    def test_requires_valid_document(self, *_):
        with pytest.raises(Exception) as context:
            generate_update_statement(-1, self.mutation_text)
        assert "does not exist" in str(context.value)

    @patch('mutate.document_ref')
    def test_requires_valid_json(self, mock_doc_ref):
        mock_doc_ref.get.return_value = [{'_id': 1}]
        with pytest.raises(Exception) as context:
            generate_update_statement(self.doc_id, '{"invalid", "json')
        assert 'must be valid json' in str(context.value)

    @patch('mutate.document_ref')
    @patch('mutate.Document')
    def test_generate_update_statement(self, mock_doc_constructor, mock_doc_ref):
        mock_doc = MagicMock()
        mock_doc_constructor.return_value = mock_doc
        mock_doc_ref.get.return_value = [{'_id': 1}]

        generate_update_statement(self.doc_id, self.mutation_text)

        mock_doc_constructor.assert_called_once()
        mock_doc.mutate.assert_called_once_with({'posts': [{'foo': 'bar'}]})


class TestDocumentApplyMutations:
    def setup_method(self):
        self.mock_ref = MagicMock()
        self.mock_transaction = MagicMock()
        self.document = Document(self.mock_ref, self.mock_transaction)

    @patch('mutate.Document.apply_add')
    def test_apply_add(self, mock_apply_add):
        self.document.mutate({"posts": [{"value": "four"}] })
        mock_apply_add.assert_called()

    @patch('mutate.Document.get_reference_by_id')
    @patch('mutate.Document.apply_delete')
    def test_apply_delete(self, mock_apply_delete, mock_get_ref):
        self.document.mutate({ "posts": [{"_id": 2, "_delete": True}] })
        mock_apply_delete.assert_called()

    @patch('mutate.Document.get_reference_by_id')
    @patch('mutate.Document.apply_update')
    def test_apply_update(self, mock_apply_update, mock_get_ref):
        self.document.mutate({ "posts": [{"_id": 2, "value": "too"}] })
        mock_apply_update.assert_called()
