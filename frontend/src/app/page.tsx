
"use client";

import { useEffect, useState } from "react";

import UploadBox from "../components/UploadBox";
import DocumentList from "../components/DocumentList";
import ChatPanel from "../components/ChatPanel";
import ComparisonPanel from "../components/ComparisonPanel";

import { API_URL } from "../lib/api";

type DocumentItem = {
  id: string;
  filename: string;
  file_type: string;
  pages: number | null;
  characters: number;
  status: string;
};

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentItem | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  async function loadDocuments() {
    try {
      const response = await fetch(
        `${API_URL}/documents/`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();
      setDocuments(data);
    } catch {
      setDocuments([]);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, [refreshKey]);

  function handleUploaded() {
    setRefreshKey((value) => value + 1);
  }

  function handleToggle(document: DocumentItem) {
    setSelectedIds((current) => {
      if (current.includes(document.id)) {
        return current.filter(
          (id) => id !== document.id
        );
      }

      return [...current, document.id];
    });
  }

  function handleSelect(document: DocumentItem) {
    setSelectedDocument(document);

    setSelectedIds((current) => {
      if (current.includes(document.id)) {
        return current;
      }

      return [document.id];
    });
  }

  const selectedDocuments = documents.filter(
    (document) =>
      selectedIds.includes(document.id)
  );

  return (
    <main className="min-h-screen bg-[#f7f9f8] text-gray-900">
      {/* Top navigation */}
      <nav className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-green-600 text-sm font-bold text-white shadow-sm">
              J
            </div>

            <div>
              <p className="text-sm font-bold tracking-tight text-gray-900">
                Juriqa
              </p>

              <p className="text-[11px] text-gray-500">
                Contract Intelligence
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-6 text-sm text-gray-500 sm:flex">
            <span>Document Analysis</span>

            <span className="h-1 w-1 rounded-full bg-gray-300" />

            <span>AI-powered</span>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-6xl px-6 py-10">
        {/* Hero */}
        <section className="mb-10">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-green-200 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
              AI contract analysis
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-gray-950 sm:text-5xl">
              Analyse your contracts
              <span className="block text-green-600">
                with AI
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-base leading-7 text-gray-600">
              Upload documents, ask questions, compare
              contracts, and get answers backed by
              verified passages from your source material.
            </p>
          </div>

          {/* Feature pills */}
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600">
              PDF & DOCX
            </span>

            <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600">
              Semantic search
            </span>

            <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600">
              Verified citations
            </span>

            <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600">
              Document comparison
            </span>
          </div>
        </section>

        {/* Upload + Documents */}
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-gray-200 bg-white p-1 shadow-sm">
            <UploadBox
              onUploaded={handleUploaded}
            />
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-1 shadow-sm">
            <DocumentList
              refreshKey={refreshKey}
              onSelect={handleSelect}
              selectedIds={selectedIds}
              onToggle={handleToggle}
            />
          </div>
        </section>

        {/* Selection status */}
        {selectedDocuments.length > 0 && (
          <div className="mt-6 flex items-center justify-between rounded-xl border border-green-200 bg-green-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-600 text-xs font-semibold text-white">
                {selectedDocuments.length}
              </span>

              <span className="text-sm font-medium text-green-800">
                {selectedDocuments.length === 1
                  ? "Document selected for analysis"
                  : `${selectedDocuments.length} documents selected for analysis`}
              </span>
            </div>

            <span className="hidden text-xs text-green-700 sm:block">
              Ready for questions
            </span>
          </div>
        )}

        {/* Chat */}
        {selectedDocuments.length > 0 && (
          <section className="mt-6">
            <ChatPanel
              documentIds={selectedDocuments.map(
                (document) => document.id
              )}
              filenames={selectedDocuments.map(
                (document) => document.filename
              )}
            />
          </section>
        )}

        {/* Comparison */}
        {documents.length >= 2 && (
          <section className="mt-8">
            <ComparisonPanel
              documents={documents}
            />
          </section>
        )}

        {/* Empty state */}
        {documents.length === 0 && (
          <div className="mt-8 rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-xl">
              📄
            </div>

            <h3 className="mt-4 text-sm font-semibold text-gray-900">
              No documents yet
            </h3>

            <p className="mx-auto mt-1 max-w-md text-sm text-gray-500">
              Upload a PDF or DOCX document above to
              start analysing it with AI.
            </p>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-14 border-t border-gray-200 pt-6">
          <div className="flex flex-col gap-2 text-xs text-gray-400 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Juriqa · AI-powered document analysis
            </span>

            <span>
              Answers are grounded in uploaded documents
            </span>
          </div>
        </footer>
      </div>
    </main>
  );
}