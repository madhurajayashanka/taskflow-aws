import { useState, useEffect, useCallback } from "react";
import { taskApi } from "../api/tasks";

const STATUS_CONFIG = {
  todo: {
    label: "To Do",
    color: "bg-amber-400",
    text: "text-amber-700",
    bg: "bg-amber-50",
  },
  in_progress: {
    label: "In Progress",
    color: "bg-blue-400",
    text: "text-blue-700",
    bg: "bg-blue-50",
  },
  done: {
    label: "Done",
    color: "bg-emerald-400",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
  },
};

export default function TaskList({ onEdit, refresh, onRefreshDone }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await taskApi.list();
      setTasks(data.results ?? data);
      setError(null);
    } catch (err) {
      setError("Failed to load tasks. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
      if (onRefreshDone) onRefreshDone();
    }
  }, [onRefreshDone]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks, refresh]);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this task?")) return;
    try {
      setDeletingId(id);
      await taskApi.delete(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      console.error("Delete failed", err);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading && tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-600">
        <p className="font-medium">{error}</p>
        <button
          onClick={fetchTasks}
          className="mt-3 text-sm font-medium text-red-700 underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 py-20">
        <svg
          className="mb-4 h-12 w-12 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <p className="text-lg font-medium text-gray-400">No tasks yet</p>
        <p className="mt-1 text-sm text-gray-400">
          Create your first task to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Title
            </th>
            <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Created
            </th>
            <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Attachment
            </th>
            <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {tasks.map((task) => {
            const cfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.todo;
            return (
              <tr
                key={task.id}
                className={`transition-colors hover:bg-gray-50 ${
                  deletingId === task.id ? "opacity-40" : ""
                }`}
              >
                {/* Title + Description */}
                <td className="px-6 py-4">
                  <p className="font-medium text-gray-900">{task.title}</p>
                  {task.description && (
                    <p className="mt-0.5 line-clamp-1 text-sm text-gray-500">
                      {task.description}
                    </p>
                  )}
                </td>

                {/* Status Badge */}
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.bg} ${cfg.text}`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${cfg.color}`} />
                    {cfg.label}
                  </span>
                </td>

                {/* Created At */}
                <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-gray-400">
                  {new Date(task.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </td>

                {/* Attachment */}
                <td className="px-6 py-4 text-sm text-gray-500">
                  {task.attachment ? (
                    <a
                      href={task.attachment}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800"
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
                          d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                        />
                      </svg>
                      File
                    </a>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>

                {/* Actions */}
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                  <button
                    onClick={() => onEdit(task)}
                    className="mr-3 font-medium text-indigo-600 transition-colors hover:text-indigo-900"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(task.id)}
                    disabled={deletingId === task.id}
                    className="font-medium text-red-500 transition-colors hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
