from dataclasses import dataclass
from pathlib import Path

@dataclass
class SourceDocument:
    id: str
    filename: str
    file_type: str
    path : str
    content: str
    
def load_doc(directory :str) -> list[SourceDocument]:
    path = Path(directory)
    documents = []
    
    for file in path.iterdir():
        if not file.is_file():
            continue
        try:
            content = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        
        documents.append(
            SourceDocument(
                id=file.stem,
                filename=file.name,
                file_type=file.suffix.lower(),
                path=file,
                content=content
            )
        )
    return documents    
