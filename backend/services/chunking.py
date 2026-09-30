import re


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    text = normalize_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary = text.rfind("\n\n", start, end)

            if boundary == -1:
                boundary = text.rfind(". ", start, end)

            if boundary > start + (chunk_size // 2):
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def create_document_chunks(content):
    chunks = []

    for item in content:
        text = item.get("text", "").strip()

        if not text:
            continue

        source = {}

        if "page" in item:
            source["page"] = item["page"]

        if "paragraph" in item:
            source["paragraph"] = item["paragraph"]

        split_chunks = split_text(text)

        for index, chunk in enumerate(split_chunks):
            chunks.append({
                "text": chunk,
                "source": source,
                "chunk_index": index
            })

    return chunks