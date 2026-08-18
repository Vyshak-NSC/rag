import os
from pypdf import PdfReader
from docx import Document
import pandas as pd

def read_pdf(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def read_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def read_xlsx(path):
    sheets = pd.read_excel(path, sheet_name=None)
    parts = []
    
    for sheet_name, df in sheets.items():
        parts.append(f"\nSheet: {sheet_name}\n{df.to_string(index=False)}")
    
    return "\n\n".join(parts)

def read_text(path):
    with open(path, 'r', encoding="utf-8", errors="ignore") as f:
        return f.read()
    
READERS = {
    ".pdf": read_pdf,
    ".docx": read_docx,
    ".xlsx": read_xlsx,
    ".txt": read_text,
}

def load_any_file(path):
    ext = os.path.splitext(path)[1].lower()
    reader = READERS.get(ext)
    if reader is None:
        return None
    return reader(path)

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # step forward, but overlap the tail
    return chunks


def ingest_folder(folder_path, store):
    ids = []
    texts = []
    metadatas = []

    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        text = load_any_file(full_path)
        if text is None:
            print(f"Skipping unsupported file: {filename}")
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".xlsx":
            pieces = [text]
        else:
            pieces = chunk_text(text)

        for i, piece in enumerate(pieces):
            ids.append(f"{filename}-{i}")
            texts.append(piece)
            metadatas.append({"source": filename})

    store.upsert(ids=ids, texts=texts, metadatas=metadatas)