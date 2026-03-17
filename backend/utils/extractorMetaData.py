from io import BytesIO
from pypdf import PdfReader
from docx import Document
from PIL import Image, ExifTags

def extract_pdf_metadata(content: bytes):
    reader = PdfReader(BytesIO(content))
    info = reader.metadata

    return {
        "title": info.title,
        "author": info.author,
        "creator": info.creator,
        "producer": info.producer,
        "creation_date": str(info.creation_date),
        "pages": len(reader.pages)
    }
    
def extract_docx_metadata(content: bytes):
    doc = Document(BytesIO(content))
    props = doc.core_properties

    return {
        "title": props.title,
        "author": props.author,
        "created": str(props.created),
        "modified": str(props.modified),
        "last_modified_by": props.last_modified_by
    }