from pathlib import Path

from pypdf import PdfReader
from docx import Document

def load_pdf(file_path):

    documents = []

    pdf = PdfReader(file_path)
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and text.strip():

            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "source": Path(file_path).name,
                        "page": page_num +1,
                        "type": "pdf",
                    },
                }
            )
    return documents
def load_docx(file_path):

    doc = Document(file_path)

    text = "\n".join(
        para.text for para in doc.paragraphs
    )

    return [
        {
            "text": text,
            "metadata": {
                "source": Path(file_path).name,
                "type": "docx",
                },
        }
    ]
def load_txt(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as f:
        
        text = f.read()
    return [
        {
            "text": text,
            "metadata": {
                "source": Path(file_path).name,
                "type": "txt",
            },
        }
    ]