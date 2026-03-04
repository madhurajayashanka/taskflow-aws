import { useState, useRef } from "react";
import { taskApi } from "../api/tasks";

export default function FileUpload({ taskId, currentFile, onUploaded }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      await taskApi.upload(taskId, file);
      if (onUploaded) onUploaded();
    } catch (err) {
      setError("Upload failed. Please try again.");
      console.error(err);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const fileName = currentFile
    ? currentFile.split("/").pop().split("?")[0]
    : null;

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">
        Attachment
      </label>

      {fileName && (
        <div className="mb-2 flex items-center gap-2 rounded-md bg-gray-50 px-3 py-2 text-sm">
          <svg
            className="h-4 w-4 flex-shrink-0 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
            />
          </svg>
          <a
            href={currentFile}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate text-indigo-600 hover:text-indigo-800"
          >
            {fileName}
          </a>
        </div>
      )}

      <div className="flex items-center gap-3">
        <label
          className={`inline-flex cursor-pointer items-center gap-2 rounded-lg border border-gray-300
            px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50
            ${uploading ? "cursor-not-allowed opacity-60" : ""}`}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
          {uploading ? "Uploading…" : "Choose File"}
          <input
            ref={inputRef}
            type="file"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
        {uploading && (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-indigo-500" />
        )}
      </div>

      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
