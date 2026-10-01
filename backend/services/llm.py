import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError

load_dotenv()


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    return genai.Client(api_key=api_key)


def get_models():
    primary_model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.7-flash"
    )

    models = [
        primary_model,
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite"
    ]

    return list(dict.fromkeys(models))


def build_prompt(question, sources):
    context_parts = []

    for index, source in enumerate(sources, start=1):
        context_parts.append(
            f"[SOURCE {index}]\n{source['text']}"
        )

    context = "\n\n".join(context_parts)

    return f"""
You are a contract analysis assistant.

Answer the user's question using ONLY the document passages provided below.

Do not use outside knowledge.
Do not invent facts.
Do not make assumptions.

Your response MUST use exactly this format:

<answer>
Your concise answer here.
</answer>

<quotes>
<quote>
Exact sentence or passage copied word-for-word from one of the provided sources.
</quote>
</quotes>

Rules:

- The answer must be supported only by the provided sources.
- Every quote must be copied exactly from the provided sources.
- Never paraphrase a quote.
- Never invent a quote.
- Use the minimum number of quotes needed.
- If the answer cannot be found in the provided sources, write:
  I could not find this information in the document.
- If the answer cannot be found, return an empty <quotes> section.
- Do not include any text outside the <answer> and <quotes> sections.

Question:
{question}

Document passages:
{context}
"""


def parse_model_response(raw_response):
    raw_response = raw_response.strip()

    answer_match = re.search(
        r"<answer>\s*(.*?)\s*</answer>",
        raw_response,
        flags=re.IGNORECASE | re.DOTALL
    )

    quote_matches = re.findall(
        r"<quote>\s*(.*?)\s*</quote>",
        raw_response,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not answer_match:
        return {
            "answer": (
                "I could not generate a valid answer "
                "from the document."
            ),
            "quotes": []
        }

    answer = answer_match.group(1).strip()

    quotes = [
        quote.strip()
        for quote in quote_matches
        if quote.strip()
    ]

    return {
        "answer": answer,
        "quotes": quotes
    }


def is_quota_error(error):
    error_text = str(error).lower()

    return (
        "resource_exhausted" in error_text
        or "quota" in error_text
        or "429" in error_text
    )


def fallback_answer(question, sources):
    """
    Safe extractive fallback used when the LLM is unavailable.

    It selects the most relevant line/passage from retrieved
    document text without inventing information.
    """

    if not sources:
        return {
            "answer": (
                "I could not find this information "
                "in the document."
            ),
            "quotes": []
        }

    question_lower = question.lower()

    question_words = [
        word.lower()
        for word in re.findall(
            r"\b[a-zA-Z0-9]+\b",
            question
        )
        if len(word) > 2
    ]

    # Words that usually represent the actual field
    # the user is asking about.
    field_keywords = [
        "university",
        "college",
        "school",
        "company",
        "organization",
        "role",
        "position",
        "degree",
        "course",
        "cgpa",
        "salary",
        "stipend",
        "location",
        "address",
        "email",
        "phone",
        "pnr",
        "train",
        "fare",
        "amount",
        "date",
        "departure",
        "arrival",
        "status"
    ]

    requested_fields = [
        word
        for word in field_keywords
        if word in question_lower
    ]

    candidate_lines = []

    for source in sources:

        text = source.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        # PDF extraction often separates useful fields
        # onto different lines, so score lines rather than
        # treating the whole chunk as one sentence.
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:

            line_lower = line.lower()

            line_words = set(
                re.findall(
                    r"\b[a-zA-Z0-9]+\b",
                    line_lower
                )
            )

            score = 0

            # General question-word overlap.
            for word in question_words:
                if word in line_words:
                    score += 1

            # Strongly prioritize the requested field.
            for field in requested_fields:
                if field in line_lower:
                    score += 8

            # Avoid returning only the person's name when
            # another line contains the requested field.
            if (
                "what is" in question_lower
                and line_lower.startswith("manvi")
                and requested_fields
                and not any(
                    field in line_lower
                    for field in requested_fields
                )
            ):
                score -= 3

            if score > 0:
                candidate_lines.append(
                    (score, line, source)
                )

    if not candidate_lines:
        return {
            "answer": (
                "I could not find this information "
                "in the document."
            ),
            "quotes": []
        }

    candidate_lines.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_score, best_line, best_source = (
        candidate_lines[0]
    )

    # If the line contains the requested field,
    # return the useful value rather than the entire line.
    answer = best_line

    # University / college extraction
    if requested_fields:

        for field in requested_fields:

            if field in (
                "university",
                "college"
            ):

                match = re.search(
                    rf"([A-Z][A-Za-z&.\- ]+{field})",
                    best_line,
                    flags=re.IGNORECASE
                )

                if match:
                    answer = (
                        match.group(1)
                        .strip()
                        .rstrip(",")
                    )

                break

    return {
        "answer": answer,
        "quotes": [best_line]
    }

def generate_answer(question, sources):
    if not sources:
        return {
            "answer": (
                "I could not find this information "
                "in the document."
            ),
            "quotes": []
        }

    prompt = build_prompt(question, sources)
    client = get_client()

    response = None

    for model in get_models():

        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                break

            except ServerError as error:

                if error.code != 503:
                    raise

                if attempt == 0:
                    time.sleep(2)

            except ClientError as error:

                if is_quota_error(error):
                    return fallback_answer(
                        question,
                        sources
                    )

                raise

        if response is not None:
            break

    if response is None:
        return fallback_answer(
            question,
            sources
        )

    raw_response = response.text or ""

    return parse_model_response(
        raw_response
    )


def stream_answer(question, sources):
    if not sources:
        yield "I could not find this information in the document."
        return

    def send_fallback():
        fallback = fallback_answer(question, sources)

        yield fallback["answer"]

        metadata = json.dumps(
            {
                "quotes": fallback["quotes"]
            },
            ensure_ascii=False
        )

        yield (
            "\n__CONTRACT_AI_CITATIONS__"
            + metadata
        )

    try:
        prompt = build_prompt(question, sources)
        client = get_client()

        for model in get_models():

            try:
                response_stream = client.models.generate_content_stream(
                    model=model,
                    contents=prompt
                )

                full_response = ""
                emitted_length = 0

                for chunk in response_stream:

                    text = getattr(chunk, "text", None)

                    if not text:
                        continue

                    full_response += text

                    start_match = re.search(
                        r"<answer>\s*",
                        full_response,
                        flags=re.IGNORECASE
                    )

                    if not start_match:
                        continue

                    answer_start = start_match.end()

                    end_match = re.search(
                        r"</answer>",
                        full_response[answer_start:],
                        flags=re.IGNORECASE
                    )

                    if end_match:
                        answer_end = (
                            answer_start + end_match.start()
                        )

                        visible_answer = full_response[
                            answer_start:answer_end
                        ]
                    else:
                        visible_answer = full_response[
                            answer_start:
                        ]

                    if len(visible_answer) > emitted_length:

                        new_text = visible_answer[
                            emitted_length:
                        ]

                        emitted_length = len(visible_answer)

                        if new_text:
                            yield new_text

                result = parse_model_response(full_response)

                if not result["answer"]:
                    yield from send_fallback()
                    return

                metadata = json.dumps(
                    {
                        "quotes": result["quotes"]
                    },
                    ensure_ascii=False
                )

                yield (
                    "\n__CONTRACT_AI_CITATIONS__"
                    + metadata
                )

                return

            except ClientError as error:

                if is_quota_error(error):
                    yield from send_fallback()
                    return

                print("Gemini client error:", error)

            except ServerError as error:

                print("Gemini server error:", error)

                if error.code == 503:
                    time.sleep(2)
                    continue

            except Exception as error:

                print(
                    f"Gemini streaming error with {model}:",
                    repr(error)
                )

                continue

        # If every Gemini model fails
        yield from send_fallback()

    except Exception as error:

        print(
            "Chat streaming failed:",
            repr(error)
        )

        yield from send_fallback()