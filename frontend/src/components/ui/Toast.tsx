import * as React from "react";
import { createContext, useContext, useState, useCallback } from "react";
import { cn } from "../../lib/cn";

// Toast types
type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

// Hook to use toast
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

// Convenience methods
export function toast(options: Omit<Toast, "id">) {
  // This will be set by the provider
  if (typeof window !== "undefined" && (window as any).__addToast) {
    (window as any).__addToast(options);
  }
}

toast.success = (title: string, description?: string) =>
  toast({ type: "success", title, description });

toast.error = (title: string, description?: string) =>
  toast({ type: "error", title, description });

toast.warning = (title: string, description?: string) =>
  toast({ type: "warning", title, description });

toast.info = (title: string, description?: string) =>
  toast({ type: "info", title, description });

// Toast Provider
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);

    // Auto-remove after duration
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Set global function for convenience
  React.useEffect(() => {
    (window as any).__addToast = addToast;
    return () => {
      delete (window as any).__addToast;
    };
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

// Toast Container
function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => onRemove(toast.id)} />
      ))}
    </div>
  );
}

// Toast Item
const typeStyles = {
  success: {
    container: "bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800",
    icon: "text-emerald-600 dark:text-emerald-400",
    iconPath: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  error: {
    container: "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800",
    icon: "text-red-600 dark:text-red-400",
    iconPath: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  warning: {
    container: "bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800",
    icon: "text-amber-600 dark:text-amber-400",
    iconPath: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
  },
  info: {
    container: "bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800",
    icon: "text-blue-600 dark:text-blue-400",
    iconPath: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
};

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const styles = typeStyles[toast.type];

  return (
    <div
      className={cn(
        "pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-lg",
        "animate-in slide-in-from-right-full fade-in duration-300",
        styles.container
      )}
      role="alert"
    >
      {/* Icon */}
      <svg
        className={cn("w-5 h-5 flex-shrink-0 mt-0.5", styles.icon)}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d={styles.iconPath} />
      </svg>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
          {toast.title}
        </p>
        {toast.description && (
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            {toast.description}
          </p>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={onClose}
        className="flex-shrink-0 p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        aria-label="Dismiss notification"
      >
        <svg
          className="w-4 h-4 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
