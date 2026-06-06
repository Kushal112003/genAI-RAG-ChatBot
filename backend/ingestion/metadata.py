"""
Document Metadata Extraction
==============================
Extracts rich metadata from uploaded files (page count, word count,
file size, timestamps) before indexing.
"""

import os
from pathlib import Path
from datetime import datetime


def extract_metadata(file_path: str) -> dict:
    """
    Extract metadata from a document file.

    Returns:
        dict with keys: filename, file_size_kb, file_type,
                        word_count, page_count, uploaded_at
    """

    path = Path(file_path)
    suffix = path.suffix.lower()

    metadata = {
        "filename": path.name,
        "file_size_kb": round(os.path.getsize(file_path) / 1024, 2),
        "file_type": suffix.lstrip("."),
        "uploaded_at": datetime.now().isoformat(),
        "word_count": 0,
        "page_count": 0,
    }

    try:
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            metadata["page_count"] = len(reader.pages)

            total_words = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                total_words += len(text.split())
            metadata["word_count"] = total_words

        elif suffix == ".docx":
            from docx import Document

            doc = Document(file_path)
            metadata["page_count"] = 1  # DOCX doesn't have physical pages
            metadata["word_count"] = sum(
                len(para.text.split()) for para in doc.paragraphs
            )

        elif suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            metadata["page_count"] = 1
            metadata["word_count"] = len(text.split())

    except Exception as e:
        metadata["extraction_error"] = str(e)

    return metadata
