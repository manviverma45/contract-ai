from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from routes.documents import documents
from services.comparison import compare_documents

router = APIRouter()


class ComparisonRequest(BaseModel):
    document_id_a: str
    document_id_b: str


@router.post("/")
def comparison(request: ComparisonRequest):
    document_a = documents.get(request.document_id_a)
    document_b = documents.get(request.document_id_b)

    if not document_a:
        raise HTTPException(
            status_code=404,
            detail="First document not found"
        )

    if not document_b:
        raise HTTPException(
            status_code=404,
            detail="Second document not found"
        )

    if request.document_id_a == request.document_id_b:
        raise HTTPException(
            status_code=400,
            detail="Please select two different documents"
        )

    return compare_documents(
        document_a,
        document_b
    )