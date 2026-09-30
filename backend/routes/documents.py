from pathlib import Path
import json
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.document_parser import extract_document
from services.chunking import create_document_chunks
from services.rag import build_index

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_FILE = BASE_DIR / "documents.json"

UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 25 * 1024 * 1024

documents = {}


def save_documents():
    data = []

    for document in documents.values():
        saved_document = {
            "id": document["id"],
            "filename": document["filename"],
            "stored_filename": document["stored_filename"],
            "file_path": document["file_path"],
            "file_type": document["file_type"],
            "pages": document["pages"],
            "characters": document["characters"],
            "content": document["content"],
            "chunks": document["chunks"],
            "status": document["status"]
        }

        data.append(saved_document)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_documents():
    if not DATA_FILE.exists():
        return

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            saved_documents = json.load(file)

        for document in saved_documents:
            file_path = Path(document["file_path"])

            if not file_path.exists():
                continue

            chunks = document.get("chunks", [])

            document["vector_index"] = build_index(chunks)
            documents[document["id"]] = document

    except Exception:
        documents.clear()


load_documents()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )
    
        # Prevent uploading the same filename more than once
    for document in documents.values():
        if document["filename"].lower() == file.filename.lower():
            raise HTTPException(
                status_code=409,
                detail="A document with this filename is already uploaded"
            )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 25 MB"
        )

    document_id = str(uuid.uuid4())

    stored_filename = f"{document_id}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    with file_path.open("wb") as buffer:
        buffer.write(content)

    try:
        extracted_content = extract_document(str(file_path))
    except Exception as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )

    if not extracted_content:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="No readable text was found in the document"
        )

    chunks = create_document_chunks(extracted_content)

    if not chunks:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="No searchable text was found in the document"
        )

    try:
        vector_index = build_index(chunks)
    except Exception as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Search index creation failed: {str(error)}"
        )

    pages = (
        len(extracted_content)
        if extension == ".pdf"
        else None
    )

    characters = sum(
        len(item.get("text", ""))
        for item in extracted_content
    )

    document = {
        "id": document_id,
        "filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_type": extension,
        "pages": pages,
        "characters": characters,
        "content": extracted_content,
        "chunks": chunks,
        "vector_index": vector_index,
        "status": "ready"
    }

    documents[document_id] = document

    save_documents()

    return {
        "id": document_id,
        "filename": file.filename,
        "file_type": extension,
        "pages": pages,
        "characters": characters,
        "chunks": len(chunks),
        "status": "ready"
    }


@router.get("/")
def list_documents():
    return [
        {
            "id": document["id"],
            "filename": document["filename"],
            "file_type": document["file_type"],
            "pages": document["pages"],
            "characters": document["characters"],
            "status": document["status"]
        }
        for document in documents.values()
    ]


@router.get("/{document_id}")
def get_document(document_id: str):
    document = documents.get(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document["id"],
        "filename": document["filename"],
        "file_type": document["file_type"],
        "pages": document["pages"],
        "characters": document["characters"],
        "status": document["status"],
        "content": document["content"]
    }

@router.delete("/{document_id}")
def delete_document(document_id: str):
    document = documents.get(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = Path(document["file_path"])

    if file_path.exists():
        file_path.unlink()

    del documents[document_id]

    save_documents()

    return {
        "message": "Document deleted successfully",
        "id": document_id
    }
