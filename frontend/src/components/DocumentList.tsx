"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../lib/api";

type DocumentItem = {
  id: string;
  filename: string;
  file_type: string;
  pages: number | null;
  characters: number;
  status: string;
};

type DocumentListProps = {
  refreshKey: number;
  onSelect: (document: DocumentItem) => void;
  selectedIds: string[];
  onToggle: (document: DocumentItem) => void;
};

export default function DocumentList({
  refreshKey,
  onSelect,
  selectedIds,
  onToggle,
}: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      setLoading(true);

      const response = await fetch(
        `${API_URL}/documents/`,
        { cache: "no-store" }
      );

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();
      setDocuments(data);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, [refreshKey]);

  async function handleDelete(document: DocumentItem) {
    const confirmed = window.confirm(
      `Delete "${document.filename}"?`
    );

    if (!confirmed) return;

    try {
      setDeletingId(document.id);

      const response = await fetch(
        `${API_URL}/documents/${document.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to delete document"
        );
      }

      setDocuments((current) =>
        current.filter(
          (item) => item.id !== document.id
        )
      );

      onToggle(document);
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : "Failed to delete document"
      );
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[290px] items-center justify-center rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <p className="text-gray-500">
          Loading documents...
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900">
        Your Documents
      </h2>

      <p className="mt-2 text-gray-500">
        Select a contract to analyse it, or select multiple
        contracts for a cross-document question.
      </p>

      {documents.length === 0 ? (
        <div className="mt-6 flex min-h-[90px] items-center justify-center rounded-xl border border-dashed border-gray-300">
          <p className="text-sm text-gray-500">
            No documents uploaded yet.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {documents.map((document) => {
            const selected = selectedIds.includes(
              document.id
            );

            const deleting =
              deletingId === document.id;

            return (
              <div
                key={document.id}
                className={`rounded-xl border p-4 transition ${
                  selected
                    ? "border-green-400 bg-green-50"
                    : "border-gray-200"
                }`}
              >
                <div className="flex items-center gap-4">
                  <input
                    type="checkbox"
                    checked={selected}
                    disabled={deleting}
                    onChange={() =>
                      onToggle(document)
                    }
                    className="h-4 w-4 accent-green-600"
                  />

                  <button
                    onClick={() =>
                      onSelect(document)
                    }
                    disabled={deleting}
                    className="min-w-0 flex-1 text-left"
                  >
                    <p className="truncate font-medium text-gray-900">
                      {document.filename}
                    </p>

                    <p className="mt-1 text-sm text-gray-500">
                      {document.file_type
                        .toUpperCase()
                        .replace(".", "")}
                      {" · "}
                      {document.pages
                        ? `${document.pages} pages`
                        : "Document"}
                      {" · "}
                      {document.characters.toLocaleString()}
                      {" characters"}
                    </p>
                  </button>

                  <span className="shrink-0 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                    {document.status}
                  </span>

                  <button
                    onClick={() =>
                      handleDelete(document)
                    }
                    disabled={deleting}
                    className="shrink-0 rounded-lg border border-red-200 px-3 py-2 text-xs font-medium text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {deleting ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedIds.length > 0 && (
        <p className="mt-4 text-sm font-medium text-green-700">
          {selectedIds.length} document
          {selectedIds.length !== 1 ? "s" : ""} selected
          for chat
        </p>
      )}
    </div>
  );
}