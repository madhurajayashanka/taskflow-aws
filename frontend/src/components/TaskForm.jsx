import { useState, useEffect } from "react";
import { taskApi } from "../api/tasks";
import FileUpload from "./FileUpload";

const INITIAL = { title: "", description: "", status: "todo" };

export default function TaskForm({ task, onClose, onSaved }) {
  const [form, setForm] = useState(INITIAL);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});

  const isEdit = Boolean(task?.id);

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title || "",
        description: task.description || "",
        status: task.status || "todo",
      });
    } else {
      setForm(INITIAL);
    }
    setErrors({});
  }, [task]);

  const validate = () => {
    const e = {};
    if (!form.title.trim()) e.title = "Title is required";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      setSaving(true);
      if (isEdit) {
        await taskApi.update(task.id, form);
      } else {
        await taskApi.create(form);
      }
      onSaved();
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === "object") {
        setErrors(data);
      } else {
        setErrors({ _general: "Something went wrong. Please try again." });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  return (
    /* Backdrop */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      {/* Modal */}
      <div className="mx-4 w-full max-w-lg rounded-xl bg-white shadow-2xl ring-1 ring-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? "Edit Task" : "New Task"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5">
          {errors._general && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
              {errors._general}
            </p>
          )}

          {/* Title */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.title}
              onChange={handleChange("title")}
              autoFocus
              className={`w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition
                focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100
                ${errors.title ? "border-red-300 bg-red-50" : "border-gray-300"}`}
              placeholder="What needs to be done?"
            />
            {errors.title && (
              <p className="mt-1 text-xs text-red-500">{errors.title}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={handleChange("description")}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition
                focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              placeholder="Add details..."
            />
          </div>

          {/* Status */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              value={form.status}
              onChange={handleChange("status")}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition
                focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          {/* File Upload (edit only) */}
          {isEdit && (
            <FileUpload
              taskId={task.id}
              currentFile={task.attachment}
              onUploaded={onSaved}
            />
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700
                transition hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm
                transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving…" : isEdit ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
