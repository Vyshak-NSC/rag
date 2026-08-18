import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.ingestion import load_doc

documents = load_doc("./docs")
for document in documents:
    print(f"\nID: {document.id}")
    print(f"File: {document.filename}")
    print(f"Type: {document.file_type}")
    print(f"Content length: {len(document.content)}")