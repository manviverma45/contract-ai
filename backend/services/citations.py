import re


def normalize_for_search(text: str) -> str:

    if not text:
        return ""

    text = text.replace(
        "\u00ad",
        ""
    )

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


def verify_quote(quote: str, content: list):

    if not quote:
        return {
            "verified": False,
            "source": None
        }

    normalized_quote = normalize_for_search(
        quote
    )

    if not normalized_quote:
        return {
            "verified": False,
            "source": None
        }

    for item in content:

        source_text = item.get(
            "text",
            ""
        )

        if not source_text:
            continue

        normalized_source = normalize_for_search(
            source_text
        )

        # Exact normalized substring match
        if normalized_quote in normalized_source:

            return {
                "verified": True,
                "source": {
                    "page": item.get("page"),
                    "paragraph": item.get("paragraph"),
                    "text": source_text
                }
            }

    # More tolerant word-based matching
    quote_words = re.findall(
        r"\b[\w@.+#-]+\b",
        normalized_quote
    )

    if len(quote_words) >= 4:

        for item in content:

            source_text = item.get(
                "text",
                ""
            )

            if not source_text:
                continue

            normalized_source = normalize_for_search(
                source_text
            )

            source_words = set(
                re.findall(
                    r"\b[\w@.+#-]+\b",
                    normalized_source
                )
            )

            matching_words = sum(
                1
                for word in quote_words
                if word in source_words
            )

            # Require a strong overlap before
            # accepting a citation.
            if (
                matching_words >= 4
                and matching_words / len(quote_words) >= 0.80
            ):

                return {
                    "verified": True,
                    "source": {
                        "page": item.get("page"),
                        "paragraph": item.get("paragraph"),
                        "text": source_text
                    }
                }

    return {
        "verified": False,
        "source": None
    }