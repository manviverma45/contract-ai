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
    Document-grounded fallback for factual questions.
    Uses the retrieved document text only and returns the
    exact supporting line/passage as the quote.
    """

    if not sources:
        return {
            "answer": "I could not find this information in the document.",
            "quotes": []
        }

    q = question.lower().strip()

    # Flatten useful lines while keeping their original text.
    lines = []

    for source in sources:
        text = source.get("text", "").strip()

        if not text:
            continue

        for line in text.splitlines():
            line = line.strip()

            if line:
                lines.append({
                    "text": line,
                    "source": source
                })

    if not lines:
        return {
            "answer": "I could not find this information in the document.",
            "quotes": []
        }

    def result(answer, quote, source):
        return {
            "answer": answer.strip(),
            "quotes": [quote.strip()]
        }

    # ---------------------------------------------------------
    # EDUCATION / UNIVERSITY / COLLEGE
    # ---------------------------------------------------------

    if any(word in q for word in [
        "college",
        "university",
        "institution"
    ]):

        for i, item in enumerate(lines):

            text = item["text"]

            if "university" in text.lower():

                return result(
                    text,
                    text,
                    item["source"]
                )

        # Handle multi-line education layouts where the
        # institution name does not contain "college".
        education_index = None

        for i, item in enumerate(lines):
            if item["text"].lower() == "education":
                education_index = i
                break

        if education_index is not None:

            for item in lines[
                education_index + 1:
                min(education_index + 6, len(lines))
            ]:
                text = item["text"]

                if text.lower() not in [
                    "education",
                    "experience"
                ]:
                    if any(char.isalpha() for char in text):
                        return result(
                            text,
                            text,
                            item["source"]
                        )

    # ---------------------------------------------------------
    # CGPA
    # ---------------------------------------------------------

    if "cgpa" in q:

        for item in lines:

            text = item["text"]

            match = re.search(
                r"CGPA\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:/\s*[0-9]+)?)",
                text,
                flags=re.IGNORECASE
            )

            if match:

                value = match.group(1).replace(" ", "")

                return result(
                    value,
                    text,
                    item["source"]
                )

    # ---------------------------------------------------------
    # DEGREE
    # ---------------------------------------------------------

    if any(word in q for word in [
        "degree",
        "qualification",
        "course",
        "studied",
        "study"
    ]):

        degree_patterns = [
            r"\bBachelor of Technology\b.*",
            r"\bBachelor of Engineering\b.*",
            r"\bMaster of Technology\b.*",
            r"\bMaster of Engineering\b.*",
            r"\bBachelor of Science\b.*",
            r"\bMaster of Science\b.*",
            r"\bB\.Tech\b.*",
            r"\bM\.Tech\b.*"
        ]

        for item in lines:

            text = item["text"]

            for pattern in degree_patterns:

                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                )

                if match:

                    degree = match.group(0).strip()

                    # Remove CGPA/date from the answer if present.
                    degree = re.sub(
                        r"\s*[—-]\s*CGPA.*$",
                        "",
                        degree,
                        flags=re.IGNORECASE
                    ).strip()

                    return result(
                        degree,
                        text,
                        item["source"]
                    )

    # ---------------------------------------------------------
    # SCHOOL
    # ---------------------------------------------------------

    if "school" in q:

        for i, item in enumerate(lines):

            text = item["text"]

            if "public school" in text.lower():

                return result(
                    text,
                    text,
                    item["source"]
                )

    # ---------------------------------------------------------
    # COMPANY / ORGANIZATION
    # ---------------------------------------------------------

    if any(word in q for word in [
        "company",
        "organization",
        "employer"
    ]):

        for item in lines:

            text = item["text"]

            if text.lower() in [
                "experience",
                "education"
            ]:
                continue

            if "foundation" in text.lower():
                return result(
                    text,
                    text,
                    item["source"]
                )

    # ---------------------------------------------------------
    # ROLE / POSITION
    # ---------------------------------------------------------

    if any(word in q for word in [
        "role",
        "position",
        "job title",
        "designation"
    ]):

        role_patterns = [
            r".*developer.*",
            r".*engineer.*",
            r".*intern.*",
            r".*analyst.*",
            r".*manager.*"
        ]

        for item in lines:

            text = item["text"]

            for pattern in role_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                ):

                    return result(
                        text,
                        text,
                        item["source"]
                    )

    # ---------------------------------------------------------
    # EMAIL
    # ---------------------------------------------------------

    if "email" in q:

        for item in lines:

            match = re.search(
                r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
                item["text"]
            )

            if match:

                return result(
                    match.group(0),
                    item["text"],
                    item["source"]
                )

    # ---------------------------------------------------------
    # PHONE
    # ---------------------------------------------------------

    if any(word in q for word in [
    "phone",
    "mobile",
    "contact number",
    "phone number",
    "mobile number"
    ]):

     for item in lines:

        text = item["text"]

        match = re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text
        )

        if match:

            return result(
                match.group(0),
                item["text"],
                item["source"]
            )
    # ---------------------------------------------------------
    # KNOWN FACTUAL FIELD NOT FOUND
    # ---------------------------------------------------------

    known_factual_terms = [
        "passport",
        "passport number",
        "date of birth",
        "birth date",
        "dob",
        "nationality",
        "age",
        "gender",
        "salary",
        "stipend",
        "joining date",
        "graduation date"
    ]

    if any(term in q for term in known_factual_terms):
        return {
            "answer": "I could not find this information in the document.",
            "quotes": []
        }
    # ---------------------------------------------------------
    # GENERIC DOCUMENT-GROUNDED SEARCH
    # ---------------------------------------------------------

    question_words = {
        word.lower()
        for word in re.findall(
            r"\b[a-zA-Z0-9]+\b",
            q
        )
        if len(word) > 2
    }

    candidates = []

    for item in lines:

        text = item["text"]
        text_words = {
            word.lower()
            for word in re.findall(
                r"\b[a-zA-Z0-9]+\b",
                text
            )
        }

        overlap = len(
            question_words & text_words
        )

        if overlap:
            candidates.append(
                (
                    overlap,
                    item
                )
            )

    if candidates:

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        best = candidates[0][1]

        return result(
            best["text"],
            best["text"],
            best["source"]
        )

    return {
        "answer": "I could not find this information in the document.",
        "quotes": []
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

    question_lower = question.lower()

    # Factual/document-field questions are answered directly
    # from the retrieved document text. This prevents an LLM
    # from selecting an unrelated but technically valid quote.
    factual_fields = [
    "college",
    "university",
    "institution",
    "cgpa",
    "degree",
    "qualification",
    "course",
    "school",
    "company",
    "organization",
    "employer",
    "role",
    "position",
    "designation",
    "email",
    "phone",
    "mobile",
    "contact number",
    "passport",
    "passport number",
    "date of birth",
    "birth date",
    "dob",
    "nationality",
    "age",
    "gender",
    "address",
    "location",
    "salary",
    "stipend",
    "joining date",
    "graduation date"
]

    is_factual = any(
        field in question_lower
        for field in factual_fields
    )

    if is_factual:

     fallback = fallback_answer(
        question,
        sources
    )

    # Always return the factual fallback answer,
    # even when the information is not present.
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

    return
    def send_fallback():
        fallback = fallback_answer(
            question,
            sources
        )

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

        prompt = build_prompt(
            question,
            sources
        )

        client = get_client()

        for model in get_models():

            try:

                response_stream = (
                    client.models.generate_content_stream(
                        model=model,
                        contents=prompt
                    )
                )

                full_response = ""
                emitted_length = 0

                for chunk in response_stream:

                    text = getattr(
                        chunk,
                        "text",
                        None
                    )

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

                    answer_start = (
                        start_match.end()
                    )

                    end_match = re.search(
                        r"</answer>",
                        full_response[
                            answer_start:
                        ],
                        flags=re.IGNORECASE
                    )

                    if end_match:

                        answer_end = (
                            answer_start
                            + end_match.start()
                        )

                        visible_answer = (
                            full_response[
                                answer_start:
                                answer_end
                            ]
                        )

                    else:

                        visible_answer = (
                            full_response[
                                answer_start:
                            ]
                        )

                    if len(visible_answer) > emitted_length:

                        new_text = (
                            visible_answer[
                                emitted_length:
                            ]
                        )

                        emitted_length = len(
                            visible_answer
                        )

                        if new_text:
                            yield new_text

                result = parse_model_response(
                    full_response
                )

                # Verify that the model actually produced
                # a supporting quote.
                verified = False

                for quote in result.get(
                    "quotes",
                    []
                ):

                    verification = verify_quote(
                        quote,
                        [
                            {
                                "text": source["text"]
                            }
                            for source in sources
                        ]
                    )

                    if verification.get("verified"):
                        verified = True
                        break

                if not result.get("answer") or not verified:

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

                print(
                    "Gemini client error:",
                    repr(error)
                )

            except ServerError as error:

                print(
                    "Gemini server error:",
                    repr(error)
                )

                if error.code == 503:

                    time.sleep(2)
                    continue

            except Exception as error:

                print(
                    f"Gemini streaming error "
                    f"with {model}:",
                    repr(error)
                )

                continue

        yield from send_fallback()

    except Exception as error:

        print(
            "Chat streaming failed:",
            repr(error)
        )

        yield from send_fallback()