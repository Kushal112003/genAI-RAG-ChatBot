from pypdf import PdfReader
from docx import Document
from pathlib import Path

def load_pdf(file_path):

    reader  = PdfReader(file_path)

    documents = []

    for page_number, page in enumerate(reader.pages):

        text = page.extract_text()

        documents.append({
            "text": text,
            "metadata":{
                "source": Path(file_path).name,
                "page": page_number + 1,
                "type": "pdf"
            }
        })
    return documents

def load_docx(file_path):

    doc = Document(file_path)

    full_text = "\n".join(
        [para.text for para in doc.paragraphs]
    )

    return [{
        "text": full_text,
        "metadata": {
            "source": Path(file_path).name,
            "type": "docx"
        }
    }]

def load_txt(file_path):

    with  open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    return [{
        "text": text,
        "metadata":{
            "source": Path(file_path).name,
            "type": "txt"
        }
    }]