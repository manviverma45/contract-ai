"use client";

import { useEffect, useState } from "react";
import { getDocument } from "../lib/api";

type SourceItem = {
  page?: number | null;
  paragraph?: number | null;
  text?: string;
};

type SourceViewerProps = {
  documentId: string;
  page: number | null;
  quote: string;
  onClose: () => void;
};

export default function SourceViewer({
  documentId,
  page,
  quote,
  onClose,
}: SourceViewerProps) {
  const [source, setSource] = useState<SourceItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSource() {
      try {
        const document = await getDocument(documentId);

        const pageContent = document.content?.find(
          (item: SourceItem) => item.page === page
        );

        setSource(pageContent || null);
      } catch {
        setSource(null);
      } finally {
        setLoading(false);
      }
    }

    loadSource();
  }, [documentId, page]);

  function renderHighlightedText(text: string) {
    if (!quote) return text;

    const normalizedText = text.toLowerCase();
    const normalizedQuote = quote.toLowerCase();

    const start = normalizedText.indexOf(normalizedQuote);

    if (start === -1) {
      return text;
    }

    const end = start + quote.length;

    return (
      <>
        {text.slice(0, start)}
        <mark className="rounded bg-yellow-200 px-1">
          {text.slice(start, end)}
        </mark>
        {text.slice(end)}
      </>
    );
  }

  return (
    <div className="mt-6 rounded-2xl border border-gray-200 bg-gray-50 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-green-600">
            Source passage
          </p>

          <h3 className="mt-1 font-semibold text-gray-900">
            Page {page || "Unknown"}
          </h3>
        </div>

        <button
          onClick={onClose}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 transition hover:bg-white"
        >
          Close
        </button>
      </div>

      {loading && (
        <p className="mt-5 text-sm text-gray-500">
          Loading source passage...
        </p>
      )}

      {!loading && !source && (
        <p className="mt-5 text-sm text-gray-500">
          The source passage could not be loaded.
        </p>
      )}

      {!loading && source && (
        <div className="mt-5 rounded-xl border border-gray-200 bg-white p-5">
          <p className="whitespace-pre-wrap text-sm leading-7 text-gray-700">
            {renderHighlightedText(source.text || "")}
          </p>
        </div>
      )}
    </div>
  );
}