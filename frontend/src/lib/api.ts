export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api";
export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Document upload failed");
  }

  return data;
}

export async function getDocuments() {
  const response = await fetch(`${API_URL}/documents/`, {
    cache: "no-store",
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch documents");
  }

  return data;
}

export async function getDocument(documentId: string) {
  const response = await fetch(
    `${API_URL}/documents/${documentId}`,
    {
      cache: "no-store",
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch document");
  }

  return data;
}

export async function askQuestion(
  documentIds: string[],
  question: string
) {
  const response = await fetch(`${API_URL}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_ids: documentIds,
      question,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to get answer");
  }

  return data;
}

type StreamCitation = {
  quote: string;
  verified: boolean;
  filename: string;
  document_id: string;
  page: number | null;
  paragraph: number | null;
};

type StreamCitationPayload = {
  quotes: StreamCitation[];
};

export async function streamQuestion(
  documentIds: string[],
  question: string,
  onChunk: (text: string) => void,
  onCitations?: (citations: StreamCitation[]) => void,
  signal?: AbortSignal
) {
  const response = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_ids: documentIds,
      question,
    }),
    signal,
  });

  if (!response.ok) {
    let message = "Failed to stream answer";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error(
      "Streaming is not supported by this response."
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  const citationMarker =
    "__CONTRACT_AI_VERIFIED__";

  let pendingText = "";
  let citationMode = false;
  let citationData = "";

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) break;

      const text = decoder.decode(value, {
        stream: true,
      });

      if (!text) continue;

      if (citationMode) {
        citationData += text;
        continue;
      }

      pendingText += text;

      const markerIndex =
        pendingText.indexOf(citationMarker);

      if (markerIndex !== -1) {
        const answerText =
          pendingText.slice(0, markerIndex);

        if (answerText) {
          onChunk(answerText);
        }

        citationData = pendingText.slice(
          markerIndex + citationMarker.length
        );

        pendingText = "";
        citationMode = true;

        continue;
      }

      const safeLength = Math.max(
        0,
        pendingText.length -
          citationMarker.length +
          1
      );

      if (safeLength > 0) {
        onChunk(
          pendingText.slice(0, safeLength)
        );

        pendingText = pendingText.slice(
          safeLength
        );
      }
    }

    const remaining = decoder.decode();

    if (remaining) {
      if (citationMode) {
        citationData += remaining;
      } else {
        pendingText += remaining;
      }
    }

    if (!citationMode && pendingText) {
      onChunk(pendingText);
    }

    if (citationMode && citationData) {
      try {
        const payload =
          JSON.parse(
            citationData
          ) as StreamCitationPayload;

        onCitations?.(
          payload.quotes || []
        );
      } catch {
        onCitations?.([]);
      }
    }
  } finally {
    reader.releaseLock();
  }
}