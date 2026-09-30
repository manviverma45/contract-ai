import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from routes.documents import documents
from services.rag import search_index
from services.llm import generate_answer, stream_answer
from services.citations import verify_quote


router = APIRouter()


class ChatRequest(BaseModel):
    document_ids: list[str]
    question: str


def get_sources(document_ids, question):
    all_sources = []

    for document_id in document_ids:
        document = documents.get(document_id)

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

        results = search_index(
            document["vector_index"],
            document["chunks"],
            question,
            top_k=6
        )

        for result in results:
            result["document_id"] = document_id
            result["filename"] = document["filename"]

            all_sources.append(result)

    all_sources.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return all_sources[:10]


def verify_quotes(quotes, document_ids):
    verified_quotes = []

    for quote in quotes:

        if not quote or not quote.strip():
            continue

        for document_id in document_ids:

            document = documents.get(document_id)

            if not document:
                continue

            verification = verify_quote(
                quote,
                document["content"]
            )

            if verification["verified"]:

                verified_quotes.append({
                    "quote": quote,
                    "verified": True,
                    "document_id": document_id,
                    "filename": document["filename"],
                    "page": verification["source"].get("page"),
                    "paragraph": verification["source"].get("paragraph"),
                    "text": verification["source"].get("text")
                })

                break

    return verified_quotes


@router.post("/")
def chat(request: ChatRequest):

    if not request.document_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one document is required"
        )

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    all_sources = get_sources(
        request.document_ids,
        request.question
    )

    if not all_sources:
        return {
            "answer": (
                "I could not find this information "
                "in the document."
            ),
            "quotes": [],
            "sources": []
        }

    result = generate_answer(
        request.question,
        all_sources
    )

    verified_quotes = verify_quotes(
        result.get("quotes", []),
        request.document_ids
    )

    if result["answer"].startswith(
        "I could not find this information"
    ):
        return {
            "answer": result["answer"],
            "quotes": [],
            "sources": []
        }

    if not verified_quotes:

        return {
            "answer": (
                "I could not verify a supporting "
                "passage for this answer."
            ),
            "quotes": [],
            "sources": []
        }

    return {
        "answer": result["answer"],
        "quotes": verified_quotes,
        "sources": verified_quotes
    }


@router.post("/stream")
def stream_chat(request: ChatRequest):

    if not request.document_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one document is required"
        )

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    all_sources = get_sources(
        request.document_ids,
        request.question
    )

    if not all_sources:

        return StreamingResponse(
            iter([
                "I could not find this information "
                "in the document."
            ]),
            media_type="text/plain"
        )

    def generate_stream():

        for chunk in stream_answer(
            request.question,
            all_sources
        ):

            # Gemini/fallback sends citation metadata
            if "__CONTRACT_AI_CITATIONS__" in chunk:

                marker = "__CONTRACT_AI_CITATIONS__"

                marker_index = chunk.find(marker)

                raw_metadata = chunk[
                    marker_index + len(marker):
                ]

                try:

                    metadata = json.loads(
                        raw_metadata
                    )

                    quotes = metadata.get(
                        "quotes",
                        []
                    )

                    verified_quotes = verify_quotes(
                        quotes,
                        request.document_ids
                    )

                    citation_payload = json.dumps(
                        {
                            "quotes": verified_quotes
                        },
                        ensure_ascii=False
                    )

                    yield (
                        "__CONTRACT_AI_VERIFIED__"
                        + citation_payload
                    )

                except Exception as error:

                    print(
                        "Citation processing error:",
                        error
                    )

                    yield (
                        "__CONTRACT_AI_VERIFIED__"
                        + json.dumps(
                            {"quotes": []}
                        )
                    )

            else:

                yield chunk

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain"
    )