"use client";

import { useState } from "react";
import { API_URL } from "../lib/api";

type UploadBoxProps = {
  onUploaded: () => void;
};

export default function UploadBox({ onUploaded }: UploadBoxProps) {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const extension = file.name.split(".").pop()?.toLowerCase();

    if (extension !== "pdf" && extension !== "docx") {
      setMessage("Only PDF and DOCX files are supported.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setMessage(`Uploaded successfully: ${data.filename}`);
      onUploaded();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Upload failed"
      );
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
      <div className="flex min-h-[290px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 px-6 text-center">
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-3xl text-green-700">
          ↑
        </div>

        <h2 className="text-xl font-semibold text-gray-900">
          Upload a contract
        </h2>

        <p className="mt-2 text-gray-500">
          PDF or DOCX files only
        </p>

        <label className="mt-7 cursor-pointer rounded-lg bg-green-600 px-7 py-3 font-medium text-white transition hover:bg-green-700">
          {uploading ? "Uploading..." : "Choose File"}

          <input
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            disabled={uploading}
            onChange={handleFileChange}
          />
        </label>

        {message && (
          <p className="mt-5 max-w-md text-sm text-gray-600">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}