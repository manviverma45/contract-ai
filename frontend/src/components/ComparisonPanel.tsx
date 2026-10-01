"use client";

import { useState } from "react";
import { API_URL } from "../lib/api";

type DocumentItem = {
  id: string;
  filename: string;
};

type Change = {
  type: string;
  old_text: string;
  new_text: string;
  old_line_start: number;
  old_line_end: number;
  new_line_start: number;
  new_line_end: number;
};

type ComparisonPanelProps = {
  documents: DocumentItem[];
};

export default function ComparisonPanel({
  documents,
}: ComparisonPanelProps) {
  const [firstDocument, setFirstDocument] = useState("");
  const [secondDocument, setSecondDocument] = useState("");
  const [changes, setChanges] = useState<Change[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function compareDocuments() {
    if (!firstDocument || !secondDocument) {
      setError("Please select two documents.");
      return;
    }

    if (firstDocument === secondDocument) {
      setError("Please select two different documents.");
      return;
    }

    setLoading(true);
    setError("");
    setChanges([]);

    try {
      const response = await fetch(
        `${API_URL}/comparison/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            document_id_a: firstDocument,
            document_id_b: secondDocument,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Comparison failed"
        );
      }

      setChanges(data.changes || []);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Comparison failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-sm font-medium text-green-600">
          Document Comparison
        </p>

        <h2 className="mt-1 text-xl font-semibold text-gray-900">
          Compare two contracts
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          Compare the extracted text and identify changes between
          two documents.
        </p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <select
          value={firstDocument}
          onChange={(event) =>
            setFirstDocument(event.target.value)
          }
          className="rounded-xl border border-gray-300 px-4 py-3 text-sm outline-none focus:border-green-500"
        >
          <option value="">Select first document</option>

          {documents.map((document) => (
            <option key={document.id} value={document.id}>
              {document.filename}
            </option>
          ))}
        </select>

        <select
          value={secondDocument}
          onChange={(event) =>
            setSecondDocument(event.target.value)
          }
          className="rounded-xl border border-gray-300 px-4 py-3 text-sm outline-none focus:border-green-500"
        >
          <option value="">Select second document</option>

          {documents.map((document) => (
            <option key={document.id} value={document.id}>
              {document.filename}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={compareDocuments}
        disabled={
          loading ||
          !firstDocument ||
          !secondDocument
        }
        className="mt-4 rounded-xl bg-green-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-300"
      >
        {loading ? "Comparing..." : "Compare Documents"}
      </button>

      {error && (
        <p className="mt-4 text-sm text-red-600">
          {error}
        </p>
      )}

      {!loading && !error && changes.length === 0 && firstDocument && secondDocument && (
        <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">
            No differences found.
          </p>
        </div>
      )}

      {changes.length > 0 && (
        <div className="mt-6 space-y-4">
          <div className="rounded-xl bg-gray-50 p-4">
            <p className="font-medium text-gray-900">
              {changes.length} change
              {changes.length !== 1 ? "s" : ""} found
            </p>
          </div>

          {changes.map((change, index) => (
            <div
              key={index}
              className="rounded-xl border border-gray-200 p-5"
            >
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium uppercase text-gray-600">
                  {change.type}
                </span>

                <span className="text-xs text-gray-400">
                  Change {index + 1}
                </span>
              </div>

              {change.old_text && (
                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-xs font-semibold uppercase text-red-600">
                    Previous
                  </p>

                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gray-700">
                    {change.old_text}
                  </p>
                </div>
              )}

              {change.new_text && (
                <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-4">
                  <p className="text-xs font-semibold uppercase text-green-600">
                    Updated
                  </p>

                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gray-700">
                    {change.new_text}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}