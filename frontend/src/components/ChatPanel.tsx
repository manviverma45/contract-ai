"use client";

import { useRef, useState } from "react";
import { streamQuestion } from "../lib/api";
import SourceViewer from "./SourceViewer";

type Citation = {
  quote: string;
  verified: boolean;
  filename: string;
  document_id: string;
  page: number | null;
  paragraph: number | null;
};

type ChatPanelProps = {
  documentIds: string[];
  filenames: string[];
};

export default function ChatPanel({
  documentIds,
  filenames,
}: ChatPanelProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedCitation, setSelectedCitation] =
    useState<Citation | null>(null);

  const abortController = useRef<AbortController | null>(null);

  async function handleAsk() {
    if (!question.trim() || loading) return;

    const currentQuestion = question.trim();

    const controller = new AbortController();
    abortController.current = controller;

    setLoading(true);
    setError("");
    setAnswer("");
    setCitations([]);
    setSelectedCitation(null);

    try {
      await streamQuestion(
        documentIds,
        currentQuestion,
        (text) => {
          setAnswer((current) => current + text);
        },
        (newCitations) => {
          if (!controller.signal.aborted) {
            setCitations(newCitations);
          }
        },
        controller.signal
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
      abortController.current = null;
    }
  }

  function handleStop() {
    abortController.current?.abort();
    abortController.current = null;
    setLoading(false);
  }

  return (
    <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-sm font-medium text-green-600">
          Contract Chat
        </p>

        <h2 className="mt-1 text-xl font-semibold text-gray-900">
          Ask about{" "}
          {filenames.length === 1
            ? filenames[0]
            : `${filenames.length} selected documents`}
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          {filenames.join(" · ")}
        </p>
      </div>

      <div className="mt-6 min-h-[180px] rounded-xl bg-gray-50 p-5">
        {!answer && !loading && !error && (
          <p className="text-sm text-gray-400">
            Ask a question about the selected documents.
          </p>
        )}

        {loading && !answer && (
          <p className="text-sm text-gray-500">
            Analysing the selected documents...
          </p>
        )}

        {error && (
          <p className="text-sm text-red-600">
            {error}
          </p>
        )}

        {answer && (
          <div>
            <div className="flex items-center gap-2">
              <p className="font-medium text-gray-900">
                Answer
              </p>

              {loading && (
                <span className="text-xs text-gray-400">
                  Generating...
                </span>
              )}
            </div>

            <p className="mt-3 whitespace-pre-wrap leading-7 text-gray-700">
              {answer}
            </p>
          </div>
        )}
      </div>

      {citations.length > 0 && (
        <div className="mt-5">
          <p className="font-medium text-gray-900">
            Verified sources
          </p>

          <div className="mt-3 space-y-3">
            {citations.map((citation, index) => (
              <button
                key={`${citation.document_id}-${index}`}
                onClick={() =>
                  setSelectedCitation(citation)
                }
                className="w-full rounded-xl border border-green-200 bg-green-50 p-4 text-left transition hover:border-green-400 hover:bg-green-100"
              >
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
                    Verified
                  </span>

                  <span className="text-xs text-gray-500">
                    {citation.filename}
                  </span>

                  {citation.page && (
                    <span className="text-xs text-gray-500">
                      Page {citation.page}
                    </span>
                  )}

                  {citation.paragraph && (
                    <span className="text-xs text-gray-500">
                      Paragraph {citation.paragraph}
                    </span>
                  )}
                </div>

                <p className="mt-3 text-sm leading-6 text-gray-700">
                  “{citation.quote}”
                </p>

                <p className="mt-2 text-xs font-medium text-green-700">
                  Click to view source →
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {answer &&
        !loading &&
        citations.length === 0 &&
        !error && (
          <div className="mt-5 rounded-xl border border-yellow-200 bg-yellow-50 p-4">
            <p className="text-sm font-medium text-yellow-800">
              No supporting passage could be verified.
            </p>
          </div>
        )}

      {selectedCitation && (
        <SourceViewer
          documentId={selectedCitation.document_id}
          page={selectedCitation.page}
          quote={selectedCitation.quote}
          onClose={() => setSelectedCitation(null)}
        />
      )}

      <div className="mt-6 flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              handleAsk();
            }
          }}
          placeholder="Ask a question about the selected documents..."
          disabled={loading}
          className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm outline-none transition focus:border-green-500 focus:ring-2 focus:ring-green-100 disabled:bg-gray-100"
        />

        {loading ? (
          <button
            onClick={handleStop}
            className="rounded-xl border border-red-300 bg-white px-6 py-3 text-sm font-medium text-red-600 transition hover:bg-red-50"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={handleAsk}
            disabled={!question.trim()}
            className="rounded-xl bg-green-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            Ask
          </button>
        )}
      </div>
    </div>
  );
}