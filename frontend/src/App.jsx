import { useState, useCallback, Component } from "react";
import TaskList from "./components/TaskList";
import TaskForm from "./components/TaskForm";

// ── Error Boundary ─────────────────────────────────────────────
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("TaskFlow Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="mx-auto max-w-md rounded-xl border border-red-200 bg-red-50 p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-red-900">
              Something went wrong
            </h2>
            <p className="mt-2 text-sm text-red-700">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function Toast({ message, onClose }) {
  return (
    <div className="fixed bottom-6 right-6 z-[60] flex items-center gap-3 rounded-lg bg-gray-900 px-5 py-3 text-sm text-white shadow-lg animate-slide-up">
      <svg
        className="h-5 w-5 flex-shrink-0 text-emerald-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 13l4 4L19 7"
        />
      </svg>
      {message}
      <button onClick={onClose} className="ml-2 text-gray-400 hover:text-white">
        ✕
      </button>
    </div>
  );
}

function AppContent() {
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [refresh, setRefresh] = useState(0);
  const [toast, setToast] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const triggerRefresh = () => setRefresh((r) => r + 1);

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const handleNew = () => {
    setEditingTask(null);
    setShowForm(true);
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    setShowForm(true);
  };

  const handleClose = () => {
    setShowForm(false);
    setEditingTask(null);
  };

  const handleSaved = () => {
    handleClose();
    triggerRefresh();
    showToast(
      editingTask ? "Task updated successfully" : "Task created successfully",
    );
  };

  const handleRefreshDone = useCallback(() => {}, []);

  return (
    <div className="flex min-h-screen">
      {/* ── Mobile Sidebar Overlay ──────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-gray-900 text-white transition-transform duration-200 md:sticky md:top-0 md:z-0 md:h-screen md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500 text-sm font-bold">
              T
            </div>
            <span className="text-lg font-semibold tracking-tight">
              TaskFlow
            </span>
          </div>
          {/* Close button (mobile only) */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="text-gray-400 hover:text-white md:hidden"
            aria-label="Close sidebar"
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

        <nav className="flex-1 px-4">
          <a
            href="#"
            className="flex items-center gap-3 rounded-lg bg-gray-800 px-3 py-2 text-sm font-medium text-white"
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            All Tasks
          </a>
        </nav>

        <div className="border-t border-gray-800 px-6 py-4 text-xs text-gray-500">
          TaskFlow v1.0 &middot; Assessment
        </div>
      </aside>

      {/* ── Main Content ────────────────────────────────────── */}
      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white/80 px-4 py-5 backdrop-blur sm:px-8">
          <div className="flex items-center gap-3">
            {/* Hamburger (mobile only) */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-1 text-gray-600 hover:bg-gray-100 md:hidden"
              aria-label="Open sidebar"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Tasks</h1>
              <p className="mt-0.5 text-sm text-gray-500">
                Manage and track your work items
              </p>
            </div>
          </div>
          <button
            onClick={handleNew}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98]"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            <span className="hidden sm:inline">New Task</span>
            <span className="sm:hidden">New</span>
          </button>
        </header>

        {/* Task List */}
        <div className="p-4 sm:p-8">
          <TaskList
            onEdit={handleEdit}
            refresh={refresh}
            onRefreshDone={handleRefreshDone}
          />
        </div>
      </main>

      {/* ── Modal ───────────────────────────────────────────── */}
      {showForm && (
        <TaskForm
          task={editingTask}
          onClose={handleClose}
          onSaved={handleSaved}
        />
      )}

      {/* ── Toast ───────────────────────────────────────────── */}
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
