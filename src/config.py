import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    "readers_file": os.path.join(BASE_DIR, "../data/users.json"),
    "reader_types_file": os.path.join(BASE_DIR, "../data/reader_types.json"),
    "reader_logs_file": os.path.join(BASE_DIR, "../data/reader_logs.json"),
    "documents_file": os.path.join(BASE_DIR, "../data/documents.json"),
    "borrow_file": os.path.join(BASE_DIR, "../data/borrow_records.json"),
    "return_file": os.path.join(BASE_DIR, "../data/return_records.json"),
    "borrowing_logs_file": os.path.join(BASE_DIR, "../data/borrowing_logs.json"),
    "document_categories_file": os.path.join(BASE_DIR, "../data/document_categories.json"),
    "document_logs_file": os.path.join(BASE_DIR, "../data/document_logs.json"),
    "document_requests_file": os.path.join(BASE_DIR, "../data/document_requests.json"),
    "library_rules_file": os.path.join(BASE_DIR, "../data/library_rules.json"),
    "logo_file": os.path.join(BASE_DIR, "../assets/logo.jpg")
}