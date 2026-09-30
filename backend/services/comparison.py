import difflib


def get_document_text(document):
    content = document.get("content", [])

    return "\n\n".join(
        item.get("text", "").strip()
        for item in content
        if item.get("text", "").strip()
    )


def compare_documents(document_a, document_b):
    text_a = get_document_text(document_a)
    text_b = get_document_text(document_b)

    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()

    matcher = difflib.SequenceMatcher(
        None,
        lines_a,
        lines_b
    )

    changes = []

    for tag, start_a, end_a, start_b, end_b in matcher.get_opcodes():
        if tag == "equal":
            continue

        changes.append({
            "type": tag,
            "old_text": "\n".join(
                lines_a[start_a:end_a]
            ),
            "new_text": "\n".join(
                lines_b[start_b:end_b]
            ),
            "old_line_start": start_a + 1,
            "old_line_end": end_a,
            "new_line_start": start_b + 1,
            "new_line_end": end_b
        })

    return {
        "document_a": document_a["filename"],
        "document_b": document_b["filename"],
        "changes": changes,
        "total_changes": len(changes)
    }