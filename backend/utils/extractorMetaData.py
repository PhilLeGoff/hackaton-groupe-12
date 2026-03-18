from io import BytesIO

def extract_pdf_metadata(content: bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        return {}

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
    try:
        from docx import Document
    except ImportError:
        return {}

    doc = Document(BytesIO(content))
    props = doc.core_properties

    return {
        "title": props.title,
        "author": props.author,
        "created": str(props.created),
        "modified": str(props.modified),
        "last_modified_by": props.last_modified_by
    }
